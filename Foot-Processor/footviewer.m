function varargout = footviewer(varargin)
% mcc -e -R -logfile -o 'FootViewer' -R 'footviewer.log' -v footviewer.m -M icon_V.res 
% mcc -e -R -logfile -o 'FootViewer' -R 'footviewer.log' -v footviewer.m -N 
% FOOTVIEWER M-file for footviewer.fig
%      FOOTVIEWER, by itself, creates a new FOOTVIEWER or raises the existing
%      singleton*.
%
%      H = FOOTVIEWER returns the handle to a new FOOTVIEWER or the handle to
%      the existing singleton*.
%
%      FOOTVIEWER('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in FOOTVIEWER.M with the given input arguments.
%
%      FOOTVIEWER('Property','Value',...) creates a new FOOTVIEWER or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before footviewer_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to footviewer_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help footviewer

% Last Modified by GUIDE v2.5 07-May-2013 06:48:34

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @footviewer_OpeningFcn, ...
                   'gui_OutputFcn',  @footviewer_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before footviewer is made visible.
function footviewer_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to footviewer (see VARARGIN)

% Choose default command line output for footviewer
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes footviewer wait for user response (see UIRESUME)
% uiwait(handles.figMain);

ud.rows = 2; ud.cols = 2;
ud.data = cell(ud.rows,ud.cols);
ud.hPlot = cell(ud.rows,ud.cols);
ud.fNames = cell(ud.rows,ud.cols);
ud.contours = 20;
ud.pathname = pwd;
set(handles.toolbar,'HandleVisibility','off');
set(handles.figMain,'UserData',ud);
redraw(handles);


% --- Outputs from this function are returned to the command line.
function varargout = footviewer_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;

function redraw(handles)

ud = get(handles.figMain,'UserData');
ud.h = subplot1(ud.rows,ud.cols,'XTickL','None','YTickL','None','Min',[0.01 0.01],'Max',[1 1],'Gap',[0.01 0.05]);
set(ud.h,'ButtonDownFcn',@(hObject, eventdata) wbd_Axes(hObject, eventdata, handles));
set(handles.figMain,'UserData',ud);
idx = 0;
for i = 1:ud.rows
	for j = 1:ud.cols
		if ~isempty(ud.data{i,j}) 
			if strcmpi(get(handles.btnContourView,'State'),'on')
				[~,ud.hPlot{i,j}] = contourf(ud.h(idx+1),ud.data{i,j}.X,ud.data{i,j}.Y,ud.data{i,j}.Z,linspace(min(ud.data{i,j}.Z(:)),max(ud.data{i,j}.Z(:)),ud.contours));
			else
				ud.hPlot{i,j} = surf(ud.h(idx+1),ud.data{i,j}.X,ud.data{i,j}.Y,ud.data{i,j}.Z,'EdgeColor','none');
			end
			title(ud.h(idx+1),ud.fNames{i,j},'interpreter', 'none');
	        set(ud.hPlot{i,j},'ButtonDownFcn',@(hObject, eventdata) wbd_Axes(hObject, eventdata, handles));
		    axis(ud.h(idx+1),'tight','off');
			daspect(ud.h(idx+1),[1,1,1]);
		end
        idx = idx+1;
	end
end
set(handles.figMain,'UserData',ud);
drawnow;


function ud = changeSize(ud)
data = cell(ud.rows,ud.cols);
data(1:size(ud.data,1),1:size(ud.data,2)) = ud.data;
ud.data = data;
hPlot = cell(ud.rows,ud.cols);
hPlot(1:size(ud.hPlot,1),1:size(ud.hPlot,2)) = ud.hPlot;
ud.hPlot = hPlot;


% --------------------------------------------------------------------
function btnAddRow_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnAddRow (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
ud.rows = min(6,ud.rows+1);
ud = changeSize(ud);
set(handles.figMain,'UserData',ud);
redraw(handles);


% --------------------------------------------------------------------
function btnRemRow_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnRemRow (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
ud.rows = max(1,ud.rows-1);
ud = changeSize(ud);
set(handles.figMain,'UserData',ud);
redraw(handles);


% --------------------------------------------------------------------
function btnAddColumn_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnAddColumn (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
ud.cols = min(6,ud.cols+1);
ud = changeSize(ud);
set(handles.figMain,'UserData',ud);
redraw(handles);


% --------------------------------------------------------------------
function btnRemColumn_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnRemColumn (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
ud.cols = max(1,ud.cols-1);
ud = changeSize(ud);
set(handles.figMain,'UserData',ud);
redraw(handles);


% --- Executes on mouse press over figure background, over a disabled or
% --- inactive control, or over an axes background.
function wbd_Axes(hObject, eventdata, handles)
% hObject    handle to figMain (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

gridsize = 150;
ud = get(handles.figMain,'UserData');
I = find(ud.h==hObject);

% axes obstructed by plot
if isempty(I) 
    for i = 1:numel(ud.h)
        hChildren = get(ud.h(i),'Children');
        if any(hChildren==hObject)
            I = i;
            break;
        end
    end
end

x = ceil(I/ud.cols);
y = I-(x-1)*ud.cols;

% right-click - remove plot
if strcmpi(get(handles.figMain,'SelectionType'),'alt')
	ud.data{x,y} = [];
    ud.hPlot{x,y} = [];
    set(handles.figMain,'UserData',ud);
    redraw(handles);
    return
end


[fname,pathname] = uigetfile({'*.asc;*.csv','All supported files'; '*.asc','ASC files'; '*.csv','CSV files'; '*.*','All files'},'Open file',ud.pathname);

if ~isequal(fname,0) && ~isequal(pathname,0)
	
	ud.fNames{x,y} = fname;
    ud.pathname = pathname;
	
	[X,Y,Z] = loadFootImage([pathname fname],gridsize);

% 	% load the data
% 	try
% 		% guess the delimiter
% 		fid = fopen([pathname fname]);
%  		str = fread(fid,4096,'*char')';
%  		fclose(fid);
%  		delimiter = guessdelim(str);
%  		if isspace(delimiter), delimiter = ''; end 
% 		
% 		% examine header row if present
% 		if isempty(regexp(str,'^\s*\*\*','once'))
% 			line = sscanf(str,'%d');
% 			if isempty(line)
% 				data = dlmread([pathname fname],delimiter,1);
% 			else
% 				data = dlmread([pathname fname],delimiter);
% 			end
% 		else
% 			str = regexp(str,'^\s*\*\*\D*\d+\D*\*\*','match');
% 			numlines = regexp(str,'\d+','match');
%  			data = dlmread([pathname fname],delimiter,[1 0 str2double(numlines{1}) 2]);
% 		end
% 		 
% 	catch ex
% 		try		% one more try
% 			data = importdata([pathname fname]);
% 			if isstruct(data), data = data.data; end
% 			data = data(:,1:3);
% 		catch ex
% 			str = sprintf('Error reading from file.\n\nException message:\n%s',ex.message);
% 			msgbox(str,'Error','error','modal');
% 			return
% 		end
% 	end
% 	
% 	data = data(:,1:3);
% 	
% 	mn = min(data); mx = max(data);
% 	xm = (mn(1):(mx(1)-mn(1))/(gridsize-1):mx(1));
% 	ym = (mn(2):(mx(2)-mn(2))/(gridsize-1):mx(2));
% 
% 	[X,Y] = meshgrid(xm,ym);
% 	Z = griddata(data(:,1),data(:,2),data(:,3),X,Y); %#ok<GRIDD>

	ud.data{x,y}.X = X;
	ud.data{x,y}.Y = Y;
	ud.data{x,y}.Z = Z;
    set(handles.figMain,'UserData',ud);
end

redraw(handles);


% --------------------------------------------------------------------
function btnExport_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnExport (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

ud = get(handles.figMain,'UserData');

% write JPEG file
filter = {'*.jpg','JPEG files'};
[fname,pathname] = uiputfile(filter,'Export JPEG file',[ud.pathname '\']);

if ~isequal(fname,0) && ~isequal(pathname,0)
	figpos = getpixelposition(handles.figMain);
	resolution = get(0,'ScreenPixelsPerInch');
	set(handles.figMain,'paperunits','inches','papersize',figpos(3:4)/resolution,'paperposition',[0 0 figpos(3:4)/resolution]);
	saveas(handles.figMain,[pathname fname],'jpg');
end


% --------------------------------------------------------------------
function btnContourView_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnContourView (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
redraw(handles);


% --------------------------------------------------------------------
function btnAddCount_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnAddCount (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
ud.contours = min(25,ud.contours+1);
set(handles.figMain,'UserData',ud);
redraw(handles);


% --------------------------------------------------------------------
function btnRemCount_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnRemCount (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
ud.contours = max(3,ud.contours-1);
set(handles.figMain,'UserData',ud);
redraw(handles);


% --------------------------------------------------------------------
function btnAbout_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnAbout (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
str{1} = 'Please report any bugs and remarks to mbudka@bournemouth.ac.uk.';
str{2} = 'Remember to include all information necessary to reproduce the undesirable behaviour (screenshots, datafile used etc.)';
str{3} = ' ';
str{4} = 'This software is for academic research purposes only.';
str{5} = ' ';
str{6} = 'MATLAB®. © 1984 – 2009 The MathWorks, Inc';
str1 = get(handles.figMain,'Name');
for i = 1:numel(str), str1 = [str1 sprintf('\n%s',str{i})]; end
msgbox(str1,'About','help','modal');
