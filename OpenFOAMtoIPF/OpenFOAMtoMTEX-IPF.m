% Input Arguments, these could be read from the keyboard
CasePath="/Users/dd/foam/dockerShared/cafoamrepo/run/ISIJ/testOrientation/"
% TimeNames=["30","60","90","120","150"]
TimeNames=["1"]
plotODF=false;
filterData=false;

% Need to loop through times folder, if we want more than just the end
% Time = 0.000381016    

% size(TimeNames,2)
% return


for time = 1:size(TimeNames,2)
    TimeName = TimeNames(time)
    eulerX = ReadFieldValues(CasePath,TimeName,"eulerX");
    % Convert eulerX to rad
    eulerX = deg2rad(eulerX);
    eulerXsize = size(eulerX)
    disp("Size of eulerX: " + eulerXsize(1))

    eulerY = ReadFieldValues(CasePath,TimeName,"eulerY");
    eulerY = deg2rad(eulerY);
    eulerYsize = size(eulerY)
    disp("Size of eulerY: " + eulerYsize(1))

    eulerZ = ReadFieldValues(CasePath,TimeName,"eulerZ");
    eulerZ = deg2rad(eulerZ);
    eulerZsize = size(eulerZ)
    disp("Size of eulerZ: " + eulerZsize(1))

    % Define crystal symmetry
    % cs = crystalSymmetry('cubic')
    cs = crystalSymmetry('m-3m');

    % Fixed crystal direction
    % r = vector3d.Z

    % Define orientation based on the eulerAngles
    ori = orientation.byEuler(eulerX,eulerY,eulerZ,cs);

    ipfKeyX=ipfHSVKey(cs);
    ipfKeyY=ipfHSVKey(cs);
    ipfKeyZ=ipfHSVKey(cs);

    ipfKeyX.inversePoleFigureDirection = vector3d.X;
    ipfKeyY.inversePoleFigureDirection = vector3d.Y;
    ipfKeyZ.inversePoleFigureDirection = vector3d.Z;

    IPFx = ipfKeyX.orientation2color(ori);
    IPFy = ipfKeyY.orientation2color(ori);
    IPFz = ipfKeyZ.orientation2color(ori);
    %}


    writeField("vector",CasePath,TimeName,"IPFx",IPFx)
    writeField('vector',CasePath,TimeName,"IPFy",IPFy)
    writeField('vector',CasePath,TimeName,"IPFz",IPFz)


    % colorR = colours(:,1);
    % colorG = colours(:,2);
    % colorB = colours(:,3);

    % writeField(CasePath,TimeName,"colorR",colorR)
    % writeField(CasePath,TimeName,"colorG",colorG)
    % writeField(CasePath,TimeName,"colorB",colorB)



    if plotODF==true
        % Plot ODF - All data
        hold on
        title('Orientation Distribution Function (ODF) for all data for time ' + TimeName + "s");
        odf = calcDensity(ori);
        plot(odf);
        mtexColorbar;
        imwrite(getframe(gcf).cdata, CasePath+TimeName+"/ODF_all.png");
        hold off

        % Plot IPF
        % figure
        hold on
        title('Inverse Pole Figure (IPF) for all data for time ' + TimeName + "s");
        % odf = calcDensity(ori)
        plotIPDF(ori,[vector3d.X,vector3d.Y,vector3d.Z],'contourf','fundamentalRegion','upper');
        mtexColorbar;
        imwrite(getframe(gcf).cdata, CasePath+TimeName+"/IPF_all.png");
        hold off
    end

    if filterData == true
        meltTime = ReadFieldValues(CasePath,TimeName,"meltTime");
        meltTimesize = size(meltTime)
        disp("Size of meltTime: " + meltTimesize(1))

        state = ReadIntFieldValues(CasePath,TimeName,"state");
        statesize = size(state)
        disp("Size of state: " + statesize(1))

        % Need to check if sizes are equal.... for now I will assume they are

        % Need to select cell values that satisfy these:
        %   meltTime > 0    this means that it is not the starting microstructure
        %   state == 2      solid cell

        % Empty array for indexs
        pC = 0;
        pickI = zeros(eulerXsize(1),1);

        for i=1:eulerXsize(1)
            if (meltTime(i)>=0) && (state(i)==2)
                pC = pC + 1;
                pickI(i) = int32(pC);
            end
        end

        % disp(pickI)

        % Create Fields for filtered data

        eulerX_filt = zeros(pC,1);
        eulerY_filt = zeros(pC,1);
        eulerZ_filt = zeros(pC,1);
        state_filt = zeros(pC,1);
        meltTime_filt = zeros(pC,1);    

        for i=1:eulerXsize(1)
        % for i=1:5
            j = int32(pickI(i));
            if j >= 1
        %         disp(j);
                eulerX_filt(j) = eulerX(i);
                eulerY_filt(j) = eulerY(i);
                eulerZ_filt(j) = eulerZ(i);
                meltTime_filt(j) = meltTime(i);
                state_filt(j) = state(i);
            end
        end
        if plotODF == true

            ori_filt = orientation.byEuler(eulerX_filt,eulerY_filt,eulerZ_filt,cs);
            % Plot ODF - Filtered data
            % figure
            hold on
            title('Orientation Distribution Function (ODF) for filtered data for time ' + TimeName + "s");
            odf = calcDensity(ori_filt);
            plot(odf)
            mtexColorbar;
            imwrite(getframe(gcf).cdata, CasePath+TimeName+"/ODF_filt.png");
            hold off

            % Plot IPF
            % figure
            hold on
            % odf = calcDensity(ori_filt)
            % plotIPDF(ori_filt,[vector3d.X,vector3d.Y,vector3d.Z],'contourf','complete','upper');
            plotIPDF(ori_filt,[vector3d.X,vector3d.Y,vector3d.Z],'contourf','fundamentalRegion','upper');
            mtexColorbar;
            % title('Inverse Pole Figure (IPF) for filtered data for time ' + TimeName + "s");
            imwrite(getframe(gcf).cdata, CasePath+TimeName+"/IPF_filt.png");
            hold off
        end
    end
end

% % % FUNCTIONS
% Function for writing RGB values to be viewed in paraview
function  writeField(ValueType,CasePath,TimeStr,FieldName,FieldValues)
    buffer={
    '/*--------------------------------*- C++ -*----------------------------------*\'
    '|=========                 |                                                 |'
    '| \\      /  F ield         | foam-extend: Open Source CFD                    |'
    '|  \\    /   O peration     | Version:     4.0                                |'
    '|   \\  /    A nd           | Web:         http://www.foam-extend.org         |'
    '|    \\/     M anipulation  |                                                 |'
    '\*---------------------------------------------------------------------------*/'
    '//             THIS FILE WAS CREATED BY D. DREELAN IN MATLAB'
    'FoamFile'
    '{'
    '    version     2.0;'
    '    format      ascii;'
    };




    iStart = size(buffer,1);
     i = iStart + 1;
     switch ValueType
         case 'vector'
            buffer{i} = '    class       "volVectorField";';
            i = i +1;
         case 'scalar'
             buffer{i} = '    class       "volScalarField";';
            i = i +1;
     end
     
     
     buffer{i} = '    location   "' + TimeStr + '";';
     i = i +1;
     buffer{i} = '    object    ' + FieldName + ';';
     i = i +1;
     buffer{i} = '}';
     i = i + 1;
     buffer{i} = 'dimensions      [0 0 0 0 0 0 0];';
     i = i + 1;
     buffer{i} = strcat('internalField   nonuniform List<',ValueType,'>');
     i = i + 1;
     buffer{i} = num2str(size(FieldValues,1));
     i = i + 1;
     buffer{i} = '(';
     i = i + 1;
     
%      ADD ALL FIELD VALUES
    switch ValueType
        case 'scalar'
            for v=1:size(FieldValues,1)
                buffer{i} = num2str(FieldValues(v));
                i = i+1;
            end
            
        case 'vector'
            for v=1:size(FieldValues,1)
%                 buffer{i} = strcat("(",num2str(FieldValues(v,1)),{" "},num2str(FieldValues(v,2)),{' '},num2str(FieldValues(v,3)),')');
                buffer{i} = "(" + num2str(FieldValues(v,1)) + " " + num2str(FieldValues(v,2)) + " " + num2str(FieldValues(v,3)) + ")";
                i = i+1;
            end
    end


     buffer{i} = ')';
     i = i + 1;

     buffer{i} = ';';
     i = i + 1;

%   ADD BOUNDARY INFOR
     buffer{i} = 'boundaryField';
     i = i + 1;
     buffer{i} = '{';
     i = i + 1;
     buffer{i} = 'frontAndBack{ type            zeroGradient;}';
     i = i + 1;
     buffer{i} = 'left{ type            zeroGradient;}';
     i = i + 1;
     buffer{i} = 'bottom{ type            zeroGradient;}';
     i = i + 1;
     buffer{i} = 'right{ type            zeroGradient;}';
     i = i + 1;
     buffer{i} = 'top{ type            zeroGradient;}';
     i = i + 1;
     buffer{i} = '}';
     i = i + 1; 

     
% PatchNames={'frontAndBack'
%     'left'
%     'bottom'
%     'right'
%     'top'
%     }     
% %      ADD PATCHES
%      for j=1:size(PatchNames)
%         buffer{i} = PatchNames(j);
%         i = i+1;
%         
%         buffer{i} = '{';
%         i = i+1;
%         buffer{i} = 'type zeroGradient;';
%         i = i+1;
%         
%         buffer{i} = '}';
%         i = i + 1;
%      end

     buffer{i} = '';
     i = i + 1;
     buffer{i} = '';
     i = i + 1;
%     END OF FILE

    disp("Writing " + FieldName + " to file")
    
    pathToFile = CasePath + TimeStr + "/" + FieldName;
    filePh = fopen(pathToFile,'w'); 
    for k=1:size(buffer,1)
      fprintf(filePh,'%s\n',buffer{k});
    end
    fclose(filePh); 
end

function fieldValues = ReadIntFieldValues(CasePath,TimeStr,FieldName)
    filePath = CasePath + TimeStr + "/" + FieldName
    lines = readlines(filePath);
    
    nLines = 0;
    
    for i=1:size(lines)
        splitLine = split(lines(i));
        if lines(i,1) == "("
%             disp(lines(i-1))
            nValues = str2num(lines(i-1));
            iStart = i+1;
        end

        if lines(i,1) == ")"
            iEnd = i-1;
        end     
    end
    
    fieldValues = zeros(nValues,1);

    for i=1:(iEnd-1)-iStart  
       fieldValues(i,1) = str2num(lines(iStart+i)); 
    end
end


function fieldValues = ReadFieldValues(CasePath,TimeStr,FieldName)
    filePath = CasePath + TimeStr + "/" + FieldName
    lines = readlines(filePath);
    
    nLines = 0;
    
    for i=1:size(lines)
        splitLine = split(lines(i));
        if lines(i,1) == "("
%             disp(lines(i-1))
            nValues = str2num(lines(i-1));
            disp(nValues)
            iStart = i;
        end

        if lines(i,1) == ")"
            iEnd = i;
        end     
    end
    
    fieldValues = zeros(nValues,1);
    disp("Size of generated field: " + size(fieldValues,1))
    
    disp("iStart: " + iStart)
    disp("iEnd: " + iEnd)
    disp("(iEnd-1) - iStart: " + ((iEnd-1)-iStart))

%     for i=iStart:iEnd
    for i=1:(iEnd-1)-iStart
%         disp(i)
        fieldValues(i,1) = str2double(lines(iStart+i)); 
    end
end