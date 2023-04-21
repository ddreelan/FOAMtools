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
    writeGradT

Description
    Read T fields from case directory, calculate gradT and write it.

Author
	Danny Dreelan
\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

int main(int argc, char *argv[])
{

#   include "setRootCase.H"


// word timeName(IStringStream(args.args()[2])());
// Info << "Time for CET: " << timeName << endl;

#   include "createTime.H"
#   include "createMesh.H"

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
    volScalarField T
    (
        IOobject
        (
            "T",
            timeName,
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        ),
        mesh
    );

        volVectorField gradT
        (
            IOobject
            (
                "gradT",
                timeName,
                mesh,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            fvc::grad(T)
        );

        gradT.write();
}

    return 0;
}


// ************************************************************************* //
