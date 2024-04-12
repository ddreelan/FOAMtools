/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | foam-extend: Open Source CFD
   \\    /   O peration     | Version:     4.0
    \\  /    A nd           | Web:         http://www.foam-extend.org
     \\/     M anipulation  | For copyright notice see file Copyright
-------------------------------------------------------------------------------
License
    This file is part of foam-extend.
    foam-extend is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation, either version 3 of the License, or (at your
    option) any later version.
    foam-extend is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with foam-extend.  If not, see <http://www.gnu.org/licenses/>.

Application
    FlatterField

Description
    Utility to flatten a 3D field in direction of patch.

Author
	Danny Dreelan
\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

int main(int argc, char *argv[])
{

//- Utility reads in the patch to flatten to, and the field that is to be flattened
argList::validArgs.append("flattenPatch");
argList::validArgs.append("fieldName");


#   include "setRootCase.H"
word patchName(IStringStream(args.args()[1])());
Info << "Patch name specified: " << patchName << endl;

word fieldName(IStringStream(args.args()[2])());
Info << "Field to be flattened: " << fieldName << endl;

#   include "createTime.H"
#   include "createMesh.H"

// Get top wall index
const label patchID = mesh.boundaryMesh().findPatchID(patchName);
if (patchID == -1)
{
    FatalError
        << "Patch not found: " << patchName << abort(FatalError);
}

// Take a references for convenience
const polyPatch& patch = mesh.boundaryMesh()[patchID];
const cellList& cells = mesh.cells();
const faceList& faces = mesh.faces();
const vectorField& points = mesh.points();
const labelList& own = mesh.faceOwner();
const labelList& nei = mesh.faceNeighbour();
    
// Get list of first set of cells
const unallocLabelList& patchFaceCells = patch.faceCells();

// Prepare list of dynamicLists, where each dynamicList will hold an ordered
// column of cell indices, and there will be one of these lists for each
// face on the top patch
PtrList< DynamicList<label> > cellColumns(patch.size());
// cellColumns = PtrList< DynamicList<label> > (topWall.size());

Info << "patchID: " << patchName << "\tID: " << patchID << "\tnCells: " << patch.size() << endl;

label approxSize(0);
// Approximate size for dynamic list intialisation
if (patch.size() > 0)
{
    approxSize = 2*mesh.nCells()/patch.size();
}

label totalCells=0;
Info << "populating cell columns" << endl;
// Populate each column
forAll(cellColumns, colI)
{
    // Initialise dynamic list using a conservative guess for the approximate
    // size
    cellColumns.set(colI, new DynamicList<label>(approxSize));

    // Take a reference to the first list
    DynamicList<label>& curCol = cellColumns[colI];

    // Add first cell
    curCol.append(patchFaceCells[colI]);

    // Now we will walk from this first cell to the bottom of the column
    // We will walk from face to opposite face in the current cell, then find
    // the next cell and repeat until we get to the opposite boundary
    label curCellID = patchFaceCells[colI];
    label curFaceID = patch.start() + colI; // global face index
    bool reachedOtherSide = false;
    do
    {
        // Take a reference to the current cell
        const cell& curCell = cells[curCellID];
        
        // Get the face at the opposite side of the cell
        // Note: this only makes sense for prism type cells
        const label nextFaceID = curCell.opposingFaceLabel(curFaceID, faces);

        if (nextFaceID == -1)
        {
            FatalError
                << "Cannot find the next face!" << abort(FatalError);
        }

        if (mesh.isInternalFace(nextFaceID))
        {
            // Find the cell at the otherside of the nextFace
            label nextCellID = -1;
            if (own[nextFaceID] == curCellID)
            {
                nextCellID = nei[nextFaceID];
            }
            else
            {
                nextCellID = own[nextFaceID];
            }

            // Add nextCellID to the current column
            curCol.append(nextCellID);

            // Update curCellID and curFaceID
            curCellID = nextCellID;
            curFaceID = nextFaceID;
        }
        else
        {
            // We have reached the boundary and are finished!
            reachedOtherSide = true;
        }
    }
    while (!reachedOtherSide);

    // Release extra unused space in the column 
    curCol.shrink();
    totalCells += curCol.size();
}
   
if (    ( totalCells != mesh.nCells() )
    )
{
    FatalError
    << "Sum of Cells in list of columns is not equal to the number of cells in mesh." << abort(FatalError);
}


Info << "Number of columns: " << cellColumns.size() << "\tpatch size: " << patch.size() << endl;


volScalarField colID
(
    IOobject
    (
        "colID",
         runTime.timeName(),
         mesh,
         IOobject::NO_READ,
         IOobject::NO_WRITE
    ),
    mesh,
    -1
);


forAll(cellColumns, i){
    forAll(cellColumns[i],j){
        label cellID = cellColumns[i][j];
        colID[cellID] = i;
    }
}
// Info << "Writing colID" << endl;
// colID.write();

//- Get list of all times
const instantList timeDirs = timeSelector::select0(runTime,args);
label timeNowIndex = 0;

// forAll(timeDirs,i){
for (int i = 1; i < timeDirs.size(); ++i)
{
    const word timeName = timeDirs[i].name();
    Info << "time i = " << i << " timeName: " << timeName << endl;
    runTime.setTime(timeDirs[i],i);
    // Info << "timeDirs[" << i << "]: " << timeDirs[i] << endl;
    //- Read desired field
    volScalarField field
    (
        IOobject
        (
            fieldName,
            timeName,
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        ),
        mesh
    );
    // Info << "Time: " << timeName << "\tavg value of field " << fieldName << " = " << gAverage(field) << endl;

    // Info << "\n\n\n\n" << endl; 

    // forAll(field, i){
    //     Info << "field[" << i << "]: " << field[i] << endl;
    // }

    // Info << "\n\n\n\n" << endl;

    // if (gAverage(field)!=1) // Field was read
    // {
        // Name of flattened field
        word flatFieldName (fieldName + word("_flat"));
        volScalarField flatField
        (
            IOobject
            (
                flatFieldName,
                timeName,
                mesh,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            mesh,
            -1
        );

        // Info << "Getting average for each cell col/row" << endl;
        // Get average for each cell col/row
        forAll(cellColumns,i){

            scalar total(0);
            label nC(0);

            // Get the current column
            const labelList& thisCol = cellColumns[i];
            // Info << "Cell col i: " << i << "\tSize: " << thisCol.size() << endl;
            forAll(thisCol,k){
                const label& thisCellI = thisCol[k];
                const scalar& val = field[thisCellI];
                // Info << "col " << i << " entry " << k << " has val = " << val << endl;
                total+=val;
                nC++;
            }

            scalar colAverage = total/nC;
            Info <<"Time " << timeName << " COLUMN " << i << " has average value of " << colAverage << endl;

            forAll(thisCol,k){
                const label& thisCellI = thisCol[k];
                flatField[thisCellI] = colAverage;
            }

            // Info << "All values in col " << i << " set to average: " << colAverage << endl;    
/*
            // Summ up the temperatures for each cell.
            scalar total(0);
            label nC(0);

            forAll(thisCol,j){
                // Info << "j: " << j << "\tcell: " << thisCol[j] << endl;
                label cellI(thisCol[j]);
                // Info << "Col "<< i << "\tCellI: " << cellI;
                // Info<< "\tval: " << field[cellI];
                total += field[cellI];
                nC++;
                // Info << "\ttotal: " << total << "\tnC: " << nC << endl;
            }


            // Info << "Calculating average" << endl;
            scalar avg = total/nC;
            // Info <<"Done" << endl;
            forAll(thisCol,k){
                Info << "k: " << k << endl;
                label cellI(thisCol[k]);
                Info << "CellI: " << cellI;
                Info << "\tfield: " << field[cellI] << endl;
                flatFieldName[cellI] = avg;
                Info << "Flat field set to " << avg << " at " << cellI << endl;
            }
            Info << "End" << endl;
*/
        }

        Info << "Writing field " << flatFieldName << " for time " << runTime.value() << endl;
        flatField.write();
    // }
    // else{
    //     Info << "Field " << fieldName << " does not exist in time directory " << timeName << ". Skipping this." << endl;
    // }

}




    return 0;
}

// ************************************************************************* //
