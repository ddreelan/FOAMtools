/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) 2018 OpenFOAM Foundation
     \\/     M anipulation  |
-------------------------------------------------------------------------------
License
    This file is part of OpenFOAM.

    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenFOAM is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.

    You should have received a copy of the GNU General Public License
    along with OpenFOAM.  If not, see <http://www.gnu.org/licenses/>.

Application
    mapMesh

Description
    Utility to map values between meshes

Author
	Danny Dreelan
\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
#include "argList.H"
// #include "mapMeshes.H"
#include "meshToMesh.H"
#include "meshToMesh0.H"
// #include "directMethod.H"
// #include "mapMeshes.H"
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

int main(int argc, char *argv[])
{

#   include "setRootCase.H"
#   include "createTime.H"

    // read the mapFieldsDict located in /case/system
    IOdictionary mapFieldsDict
    (
        IOobject
        (
            "mapFieldsDict",
            runTime.system(),
            runTime,
            IOobject::MUST_READ,
            IOobject::NO_WRITE,
            false
        )
    );

    HashTable<word> patchMap;
    wordList cuttingPatches;
    mapFieldsDict.lookup("patchMap") >> patchMap;
    mapFieldsDict.lookup("cuttingPatches") >>  cuttingPatches;

    Switch refineMesh(mapFieldsDict.lookup("refineMesh"));
    // Need to use "mesh" as the mapped region mesh if true,
    // if false, just use the original mesh.

    // fvMesh mesh();
    // fvMesh srcMesh();
    Foam::autoPtr<Foam::fvMesh> meshPtr(nullptr);
    Foam::autoPtr<Foam::fvMesh> srcMeshPtr(nullptr);

    if (refineMesh)
    {
        // Make the standard "mesh" the refined / mapped one
        meshPtr.reset
        (
            new Foam::fvMesh
            (
                Foam::IOobject
                (
                    word("mappedMesh"),
                    runTime.timeName(),
                    runTime,
                    IOobject::MUST_READ
                )
            )
        );

        // Make the "srcMesh" the default (in time dirs, not in sub-folders)
        srcMeshPtr.reset
        (
            new Foam::fvMesh
            (
                Foam::IOobject
                (
                    Foam::polyMesh::defaultRegion,
                    runTime.timeName(),
                    runTime,
                    IOobject::MUST_READ
                )
            )
        );
    }

    else{
        // Make the standard "mesh" the default (in time dirs, not in sub-folders)
        meshPtr.reset
        (
            new Foam::fvMesh
            (
                Foam::IOobject
                (
                    Foam::polyMesh::defaultRegion,
                    runTime.timeName(),
                    runTime,
                    IOobject::MUST_READ
                )
            )
        );
        srcMeshPtr.reset
        (
            new Foam::fvMesh
            (
                Foam::IOobject
                (
                    Foam::polyMesh::defaultRegion,
                    runTime.timeName(),
                    runTime,
                    IOobject::MUST_READ
                )
            )
        );
    }

    Foam::fvMesh& srcMesh = srcMeshPtr();
    Foam::fvMesh& mesh = meshPtr();

    Info << "MESHES SET: Source = " << srcMesh.nCells() << " cells\tTarget = " << mesh.nCells() << " cells" << endl;


    // If not refining the mesh, use the direct mapMethod which is much faster
    word mapMethod("direct");
    if (refineMesh)
    {
        mapMethod = word("cellVolumeWeight");
    }

    // Create the interpolation scheme
    meshToMesh meshToMeshInterp
    (
        srcMesh,
        mesh,
        mapMethod,
        patchMap,
        cuttingPatches
    ); 


    Info<< "Source mesh size: " << srcMesh.nCells() << "\t\tTarget mesh size: " << mesh.nCells() << endl;

    // Get list of times in the case directory
    const instantList timeDirs = timeSelector::select0(runTime,args);

    forAll(timeDirs,timeI){
        runTime.setTime(timeDirs[timeI],timeI);
        Info<< nl<< "Mapping fields for time " << runTime.timeName() << endl;

        Info << "Reading T field from source mesh..." << endl;
        volScalarField Tsrc
        (
            IOobject
            (
                "T",
                runTime.timeName(),
                srcMesh,
                IOobject::MUST_READ,
                IOobject::NO_WRITE
            ),
            srcMesh
        );

        Info << "Creating T field from target mesh..." << endl;

        volScalarField T
        (
            IOobject
            (
                "T",
                runTime.timeName(),
                mesh,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            mesh,
            0.0,
            zeroGradientFvPatchScalarField::typeName
        );

        Info << "Interpolating field from source field (size = " << Tsrc.size() 
        << ") to target (size = " << T.size() << ")" << endl;

        Info << "BEFORE MAPPING source field max: " << gMax(Tsrc) << "\tmin: " << gMin(Tsrc) << "\tavg: " << gAverage(Tsrc) << endl;
        Info << "BEFORE MAPPING target field max: " << gMax(T) << "\tmin: " << gMin(T) << "\tavg: " << gAverage(T) << endl;        
        
        // if (refineMesh)
        // {
            meshToMeshInterp.mapSrcToTgt
            (
                Tsrc, //source field
                T //target field
            );
        // }
        // else{
        //     T = Tsrc;
        // }

        Info << "AFTER MAPPING source field max:  " << gMax(Tsrc) << "\tmin: " << gMin(Tsrc) << "\tavg: " << gAverage(Tsrc) << endl;
        Info << "AFTER MAPPING target field max:  " << gMax(T) << "\tmin: " << gMin(T) << "\tavg: " << gAverage(T) << endl;

        Info << "Interpolation finished, writing mapped T for time " << runTime.timeName() << endl;
        T = T*0.5;
        T.write();
    }
    
    Info << "Mapping complete" << endl;
    return 0;
}

// ************************************************************************* //
