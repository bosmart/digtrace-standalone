% References: Yaw, pitch and roll rotations:
% http://planning.cs.uiuc.edu/node102.html
% Image converter: http://www.coolutils.com/Online/Image-Converter/
% Compilation (R2014a): 
%   addpath 'C:\Dropbox\Consultancy\Applied Sciences\FootUtils\'; 
%   mcc -e -R -logfile -o 'FootProcessor' -R 'footprocessor.log' -v footprocessor.m -a logo_fp.png -N -p 'stats\'
%
% http://www.mathworks.co.uk/products/compiler/mcr/
%
% Change log:
% 1.23
% - fixed a save file bug (didn't allow to save if no landmarks defined)
%
% 1.22
% - added ability to plot contour lines on landmarks and caclulate the area
%
% 1.21
% - added "move origin to landmark" on export
%
% 1.20
% - grid generated and interpolated using MATLAB TriScatteredInterp (fast!)
% - grid buffer removed to save memory
% - interplation error calculation
% - landmark preview now supports JPEG file export
% - tape measure has been added to the contour map
% - additional save options: remove nans, normalise, resample from grid
% - export current view to JPEG
%
% FIX - countour slider density position is not taken into accunt when swithcing to landmark/autocountour mode
% FIX - Countour slider works strangely
% FIX - AutoRotate crashes on NaNs - add a NaN check
% FIX - left-click on a landmark point causes an exception
% FIX - guides buttons stop wrking
%
% 1.10
% - renamed to "Foot Processor"
% - new logo
% - fill axis button
% - contour plot (+ density) 
% - landmarks tool
% - reset landmarks button
% - preview landmarks button + window with copy/export functionality
% TODO
%- limit grid resolution


function varargout = footprocessor(varargin)
	% FOOTPROCESSOR M-file for footprocessor.fig
	%      FOOTPROCESSOR, by itself, creates a new FOOTPROCESSOR or raises the existing
	%      singleton*.
	%
	%      H = FOOTPROCESSOR returns the handle to a new FOOTPROCESSOR or the handle to
	%      the existing singleton*.
	%
	%      FOOTPROCESSOR('CALLBACK',hObject,eventData,handles,...) calls the local
	%      function named CALLBACK in FOOTPROCESSOR.M with the given input arguments.
	%
	%      FOOTPROCESSOR('Property','Value',...) creates a new FOOTPROCESSOR or raises the
	%      existing singleton*.  Starting from the left, property value pairs are
	%      applied to the GUI before footprocessor_OpeningFcn gets called.  An
	%      unrecognized property name or invalid value makes property application
	%      stop.  All inputs are passed to footprocessor_OpeningFcn via varargin.
	%
	%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
	%      instance to run (singleton)".
	%
	% See also: GUIDE, GUIDATA, GUIHANDLES
	% Copyright 2002-2006 The MathWorks, Inc.
	% Edit the above text to modify the response to help footprocessor
	% Last Modified by GUIDE v2.5 04-Jan-2013 12:37:44

	% Begin initialization code - DO NOT EDIT
	gui_Singleton = 1;
	gui_State = struct('gui_Name',       mfilename, ...
					   'gui_Singleton',  gui_Singleton, ...
					   'gui_OpeningFcn', @footprocessor_OpeningFcn, ...
					   'gui_OutputFcn',  @footprocessor_OutputFcn, ...
					   'gui_LayoutFcn',  [] , ...
					   'gui_Callback',   []);
	if nargin && ischar(varargin{1})
		gui_State.gui_Callback = str2func(varargin{1});
	end

	if nargout
		[varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
	else
		gui_mainfcn(gui_State, varargin{:});
	end % End initialization code - DO NOT EDIT
end

% --- Executes just before footprocessor is made visible.
function footprocessor_OpeningFcn(hObject, eventdata, handles, varargin)
	% This function has no output args, see OutputFcn.
	% hObject    handle to figure
	% eventdata  reserved - to be defined in a future version of MATLAB
	% handles    structure with handles and user data (see GUIDATA)
	% varargin   command line arguments to footprocessor (see VARARGIN)

	% Choose default command line output for footprocessor
	handles.output = hObject;

	% Update handles structure
	guidata(hObject, handles);

	% center the window on the (first) screen
	[~,pos] = centerFigure(handles.figMain);
	movegui(handles.figMain,'center');
	orgUnits = get(handles.figMain,'Units');
	set(handles.figMain,'Units','pixels');
	pos1 = get(handles.figMain,'Position');
	pos(2) = pos1(2);
	set(handles.figMain,'Position',pos);
	set(handles.figMain,'Units',orgUnits);

	% display the logo
	ud.axMainPos = get(handles.axMain,'Position');
	orgUnits = get(handles.axMain,'Units');
	set(handles.axMain,'Units','pixels');
	pixPos = get(handles.axMain,'Position');
	bg = get(handles.figMain,'Color');
	rgb = imread('logo_fp.png','BackgroundColor',bg);
	[imH,imW] = size(rgb);
	if (imW<pixPos(3) && imH<pixPos(4))
		imX = round(pixPos(1)+pixPos(3)/2 - imW/2);
		imY = round(pixPos(2)+pixPos(4)/2 - imH/2);
		set(handles.axMain,'Position',[imX imY imW imH]);
	end
	image(rgb);
	axis image;
	set(handles.axMain,'Visible','off');
	set(handles.axMain,'Units',orgUnits);

	ud.contours = get(handles.slContours,'Value');
	
	% load saved configuration
	try
		s = load(mfilename);

		set(handles.slGridSize,'Value',s.status.gridsize);
		set(handles.ddPlotType,'Value',s.status.plottype);
		set(handles.ddColormap,'Value',s.status.colormap);
		ud.pathname = s.status.pathname;
		if isfield(s.status,'pathnameLandmark') && ~isempty(s.status.pathnameLandmark)
			ud.pathnameLandmark = s.status.pathnameLandmark;
		else
			ud.pathnameLandmark = ud.pathname;
		end
		set(handles.slContours,'Value',s.status.contours);
		ud.contours = s.status.contours;
		
	catch ex
		fname = mfilename('fullpath');
		idx = strfind(fname,'\');
		ud.pathname = fname(1:idx(end));
		ud.pathnameLandmark = ud.pathname;
	end

	% set default gridsize for fast rendering of data
	g = num2str(get(handles.slGridSize,'Value'));
	set(handles.txtGridSize,'String',[g ' x ' g]);
	
	% set default contour space
	cs = num2str(get(handles.slContours,'Value'));
	set(handles.txtContours,'String',cs);

	% initializie various variables
	ud.version = '1.23';
	ud.windowName = [get(handles.figMain,'Name') ' ' ud.version];
	set(handles.figMain,'Name',ud.windowName);
	ud.viewpoints = [get(handles.axXZ,'View'); get(handles.axYZ,'View'); get(handles.axXY,'View'); -37.5 30.0];
	ud.info{1} = 'Please report any bugs and remarks to mbudka@bournemouth.ac.uk.';
	ud.info{2} = 'Remember to include all information necessary to reproduce the undesirable behaviour (screenshots, datafile used etc.)';
	ud.info{3} = ' ';
	ud.info{4} = 'This software is for academic research purposes only.';
	ud.info{5} = ' ';
	ud.info{6} = 'MATLAB®. © 1984 – 2015 The MathWorks, Inc';
	ud.info{7} = ' ';
	ud.info{8}  = 'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"';
    ud.info{9}  = 'AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE';
    ud.info{10} = 'IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE';
    ud.info{11} = 'ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE';
    ud.info{12} = 'LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR';
    ud.info{13} = 'CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF';
    ud.info{14} = 'SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS';
    ud.info{15} = 'INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN';
    ud.info{16} = 'CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)';
    ud.info{17} = 'ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE';
    ud.info{18} = 'POSSIBILITY OF SUCH DAMAGE.';

	setappdata(handles.figMain,'version',ud.version);
	setappdata(handles.figMain,'info',ud.info);
	set(handles.figMain,'UserData',ud);

	% display info in console window
	% disp(' '); disp([ud.windowName ' v' ud.version]); disp(' ');
	% cellfun(@(x) disp(x),ud.info);
end

% --- Outputs from this function are returned to the command line.
function varargout = footprocessor_OutputFcn(hObject, eventdata, handles) 
	% varargout  cell array for returning output args (see VARARGOUT);
	% hObject    handle to figure
	% eventdata  reserved - to be defined in a future version of MATLAB
	% handles    structure with handles and user data (see GUIDATA)

	% Get default command line output from handles structure
	varargout{1} = handles.output;
end

% --- Executes during object deletion, before destroying properties.
function figMain_DeleteFcn(hObject, eventdata, handles)
% hObject    handle to figMain (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
if isfield(ud,'modified') && (ud.modified==1) && strcmpi(confirmSave,'Yes')
	menuitemSave_Callback(hObject, eventdata, handles); 
end
ud = get(handles.figMain,'UserData');
if ~isfield(ud,'pathname'), ud.pathname = pwd; end
status.gridsize = get(handles.slGridSize,'Value');
status.plottype = get(handles.ddPlotType,'Value');
status.colormap = get(handles.ddColormap,'Value');
status.pathname = ud.pathname;
status.contours = get(handles.slContours,'Value');

fname = mfilename('fullpath');
save(fname,'status');

if isfield(ud,'hFigToClose') && ~isempty(ud.hFigToClose), close(ud.hFigToClose(ishandle(ud.hFigToClose))); end

end

% USER FUNCTIONS ----------------------------------------------

function [screensize,pos] = centerFigure(h)
orgUnits = get(h,'Units');
set(h,'Units','pixels');
pos = get(h,'Position');
screensize = get(0,'MonitorPositions'); screensize = screensize(1,:);
xpos = ceil((screensize(3)-pos(3))/2); % center the figure on the screen horizontally
ypos = ceil((screensize(4)-pos(4))/2); % center the figure on the screen vertically
pos = [xpos ypos pos(3) pos(4)];
set(h,'Position',pos);
set(h,'Units',orgUnits);
end

function choice = confirmSave
	choice = questdlg('Do you want to save the current file?', ...
		'Confirm operation','Yes','No','Yes');
end

function ud = updatePlots(handles,updateall,plottype,hAx)	% hFig - alternate handle for the main plot

ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data'), return; end

if (nargin<2) || isempty(updateall), updateall = true; end
if (nargin<3) || isempty(plottype), plottype = get(handles.ddPlotType,'Value'); end
if (nargin<4) || isempty(hAx), hAx = handles.axMain; end

if strcmpi(get(handles.btnContour,'State'),'on'), 
	landmarkMode = true;
	plottype = 4;
else
	landmarkMode = false;
end

if strcmpi(get(handles.btnContourCrop,'State'),'on'),
    contourCropMode = true;
	plottype = 4;
else
    contourCropMode = false;
end

if strcmpi(get(handles.btnSelectPolygonTool,'State'),'on'), 
	polygonMode = true;
else
	polygonMode = false;
end

g = get(handles.slGridSize,'Value');
[ud.X,ud.Y,ud.Z] = generateGrid(g,ud,strcmpi(get(handles.btnOldGrid,'State'),'on')); 

if hAx == handles.axMain
	ud.hPCs = displayFrame(ud.hPCs,0);
	ud.hGuides = displayFrame(ud.hGuides,0);
end
ud.hCropRect = [];
ud.hLandmarks = [];

set(handles.figMain,'UserData',ud);
if hAx == handles.axMain
	showMoreGuides(handles,[],0);
end

currView = get(handles.axMain,'View');

if isequal(currView,[0 90]), currView = ud.viewpoints(end,:); end
if landmarkMode || polygonMode || contourCropMode
	currView = [0 90];
	currAxis = axis;
%	currpbAspect = pbaspect;
	currdAspect = daspect;
end

if plottype==4, set(handles.slContours,'Enable','on');
else set(handles.slContours,'Enable','off');
end

switch (plottype)
	case 1 
 		h = surf(hAx,ud.X,ud.Y,ud.Z,'EdgeColor','none');
	case 2 
		h = surf(hAx,ud.X,ud.Y,ud.Z);
	case 3 
		h = mesh(hAx,ud.X,ud.Y,ud.Z);
	case 4
		if numel(ud.contours) == 1, v = linspace(min(ud.data(:,3)),max(ud.data(:,3)),ud.contours+2);
		else v = ud.contours;
		end
		if landmarkMode || contourCropMode
			[C,h] = contourf(hAx,ud.X,ud.Y,ud.Z,v);
            
			if landmarkMode && isfield(ud,'landmarkPts') && ~isempty(ud.landmarkPts)
				if isfield(ud,'hLandmarks') && ~isempty(ud.hLandmarks)
					delete(ud.hLandmarks);
				end
				hold(hAx,'on');
				hLandmarks = nan(1,size(ud.landmarkPts,1));
				for i = 1:size(ud.landmarkPts,1)
					hLandmarks(i) = plot(hAx,ud.landmarkPts(i,1),ud.landmarkPts(i,2),'.','MarkerSize',20,'MarkerFaceColor','b');
				end
				hold(hAx,'off');
			end
		else
			[C,h] = contour3(hAx,ud.X,ud.Y,ud.Z,v);
		end
end
set(hAx,'Visible','off');
if hAx == handles.axMain
	colorbar('SouthOutside');
end
ud = get(handles.figMain,'UserData'); 
ud.axMainPos = get(handles.axMain,'Position'); 
ud.hMainPlot = h;
if exist('hLandmarks','var'), ud.hLandmarks = hLandmarks; end
if exist('C','var'), ud.C = C; end
set(handles.figMain,'UserData',ud);
ud.hl = [];
ud.polyPts = [];
% xlabel(handles.axMain,'x'); ylabel(handles.axMain,'y'); zlabel(handles.axMain,'z');
% set(handles.axMain,'XTickLabel',[]); set(handles.axMain,'YTickLabel',[]); set(handles.axMain,'ZTickLabel',[]);
set(hAx,'View',currView);
if hAx == handles.axMain
	btnShowGuides_Callback(handles.btnShowGuides, hAx, handles);
	btnShowMoreGuides_Callback(handles.btnShowMoreGuides, hAx, handles);
end

updateColormap(handles);

if landmarkMode || polygonMode
	daspect(hAx,currdAspect);	
	axis(hAx,currAxis);
else
	axis(hAx,'equal');
	if ~contourCropMode, 
		axis(hAx,'tight');
	end
end

if (updateall)
	axHandles = [handles.axXZ handles.axYZ handles.axXY];
	
	for i = 1:3
		mesh(axHandles(i),ud.X,ud.Y,ud.Z);
		set(axHandles(i),'Visible','off');
		btnShowGuides_Callback(handles.btnShowGuides, axHandles(i), handles);
		btnShowMoreGuides_Callback(handles.btnShowMoreGuides, axHandles(i), handles);
		set(axHandles(i),'View',[ud.viewpoints(i,1) ud.viewpoints(i,2)]);
 		axis(axHandles(i),'equal'); axis(axHandles(i),'tight');
	end
	
end
if hAx == handles.axMain
	btnShowPCs_Callback(handles.btnShowPCs,hAx,handles);
end

%if ~contourCropMode, axis(handles.axMain,'fill'); end

end

function updateColormap(handles)

contents = cellstr(get(handles.ddColormap,'String'));
cmap = get(handles.ddColormap,'Value');
eval(['colormap ' contents{cmap}]);
end

function [mm,centr] = getMinMaxCenter(data)
centr = mean(data,1);
mm = [min(data,[],1); max(data,[],1)];
end

function p = getFrameCoord(mm,c)
	
p = [mm(1,1) mm(1,2) c(3);	mm(2,1) mm(1,2) c(3);
	c(1) mm(1,2) mm(1,3);	c(1) mm(1,2) mm(2,3);
	mm(1,1) mm(1,2) c(3);	mm(1,1) mm(2,2) c(3);
	mm(1,1) c(2) mm(1,3);	mm(1,1) c(2) mm(2,3);
	mm(1,1) c(2) mm(2,3);	mm(2,1) c(2) mm(2,3);
	c(1) mm(1,2) mm(2,3);	c(1) mm(2,2) mm(2,3);
	mm(1,1) mm(2,2) c(3);	mm(2,1) mm(2,2) c(3);
	c(1) mm(2,2) mm(1,3);	c(1) mm(2,2) mm(2,3);
	mm(2,1) mm(1,2) c(3);	mm(2,1) mm(2,2) c(3);
	mm(2,1) c(2) mm(1,3);	mm(2,1) c(2) mm(2,3);
	mm(1,1) c(2) mm(1,3);	mm(2,1) c(2) mm(1,3);
	c(1) mm(1,2) mm(1,3);	c(1) mm(2,2) mm(1,3)];
end

function showMoreGuides(handles,axHandles,show)

ud = get(handles.figMain,'UserData');

%delete old arrows if visible
if (show==0) && isfield(ud,'hMoreGuides') && ~isempty(ud.hMoreGuides)
	
	if ishandle(ud.hMoreGuides), delete(ud.hMoreGuides); end
	ud.hMoreGuides = [];

elseif (show==1)
	
	mm = getMinMaxCenter(ud.data);
	if ~isfield(ud,'hMoreGuides'), ud.hMoreGuides = []; end
	ud.hMoreGuides(~ishandle(ud.hMoreGuides)) = [];
	
	for i = 1:numel(axHandles)
		hold(axHandles(i),'on');

		% even more
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(2,1)],[mm(1,2) mm(1,2)],[mm(1,3) mm(1,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(2,1)],[mm(1,2) mm(1,2)],[mm(2,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(1,1)],[mm(1,2) mm(2,2)],[mm(1,3) mm(1,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(1,1)],[mm(1,2) mm(2,2)],[mm(2,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(2,1)],[mm(1,2) mm(1,2)],[mm(2,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(2,1)],[mm(2,2) mm(2,2)],[mm(2,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(2,1)],[mm(2,2) mm(2,2)],[mm(1,3) mm(1,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(2,1)],[mm(2,2) mm(2,2)],[mm(2,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(2,1) mm(2,1)],[mm(1,2) mm(2,2)],[mm(1,3) mm(1,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(2,1) mm(2,1)],[mm(1,2) mm(2,2)],[mm(2,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(1,1)],[mm(1,2) mm(1,2)],[mm(1,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(2,1) mm(2,1)],[mm(1,2) mm(1,2)],[mm(1,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(1,1) mm(1,1)],[mm(2,2) mm(2,2)],[mm(1,3) mm(2,3)],'k--');
		ud.hMoreGuides(end+1) = plot3(axHandles(i),[mm(2,1) mm(2,1)],[mm(2,2) mm(2,2)],[mm(1,3) mm(2,3)],'k--');

		hold(axHandles(i),'off');
 		axis(axHandles(i),'equal'); axis(axHandles(i),'tight');
	end
	
	set(ud.hMoreGuides,'HitTest','off');

end

set(handles.figMain,'UserData',ud);
end

function [hSl,hTxt,status] = modifyRotSliders(handles,operation)

hSl = [handles.slYaw handles.slPitch handles.slRoll];
hTxt = [handles.txtYaw handles.txtPitch handles.txtRoll];
status = get(hSl(1),'Enable');
switch(operation)
	case 'reset'
		set(hSl,'Value',0);	set(hTxt,'String','0.000');
		set(hSl,'Enable','on');
		set(hTxt,'Enable','on');
	case 'enable'
		set(hSl,'Enable','on');
		set(hTxt,'Enable','on');
	case 'disable'
		set(hSl,'Enable','off');
		set(hTxt,'Enable','off');
end
drawnow;
end

function hFrame = displayFrame(hFrame,show,p,style,axHandles)

if (show==0) && ~isempty(hFrame)
	if ishandle(hFrame), delete(hFrame); end
	hFrame = [];
elseif (show==1)
	for i = 1:numel(axHandles)
		h = zeros(1,size(p,1)/2);
		hold(axHandles(i),'on');
		for j = 1:size(p,1)/2
			k = 1 + 2*(j-1);
			h(j) = plot3(axHandles(i),[p(k,1) p(k+1,1)],[p(k,2) p(k+1,2)],[p(k,3) p(k+1,3)],style{1},'LineWidth',style{2});
		end
		hold(axHandles(i),'off'); axis(axHandles(i),'equal'); axis(axHandles(i),'tight');
		hFrame = [hFrame h];
	end
	set(hFrame,'HitTest','off');
end
end

function PCs = calcPCs(data)
% PCs = princomp(data)'; 
data = bsxfun(@minus,data,nanmean(data,1));
data(isnan(data(:,3)),:) = [];
[PCs,dummy] = eig(data'*data); 
PCs = fliplr(PCs)';
end

function data = rotateData(data,R)
c = ones(size(data,1),1) * nanmean(data,1);
data = c + (data-c)*R';
data(all(isnan(data),2),:) = [];
end

function modified = setModified(modified,enable,handles,fname,windowName)

if (enable==1) && (modified==0)
	set(handles.figMain,'Name',[get(handles.figMain,'Name') '*']);
	modified = 1;
elseif (enable==0)
	if (nargin<4), fname = ud.fname; end
	set(handles.figMain,'Name',[windowName ' - ' fname]);
	modified = 0;
end
end

function [X,Y,Z] = flipGrid(X,Y,Z,idx,centr)

	if ~isempty(X)
		g = length(X);
		c = ones(g*g,1)*centr;
		switch (idx)
			case 1
				X = reshape(2*c(idx) - X(:),g,g);
			case 2
				Y = reshape(2*c(idx) - Y(:),g,g);
			case 3
				Z = 2*centr(idx) - Z;
		end
	end
end

function [X,Y,Z] = rotateGrid(X,Y,Z,centr,R)

	if ~isempty(X)
		data = [X(:) Y(:) Z(:)];
		c = ones(length(data),1)*centr;
		data = c + (data-c)*R';
		X = reshape(data(:,1),sqrt(length(data)),sqrt(length(data)));
		Y = reshape(data(:,2),sqrt(length(data)),sqrt(length(data)));
		Z = reshape(data(:,3),sqrt(length(data)),sqrt(length(data)));
	end
	
end

function [X,Y,Z] = generateGrid(gridsize,ud,oldGrid)

	h = waitbar(0,'Generating grid for plotting. Please wait...','Visible','off');	%,'WindowStyle','modal');
	centerFigure(h); set(h,'Visible','on');

	mn = min(ud.data); mx = max(ud.data);
	x = (mn(1):(mx(1)-mn(1))/(gridsize-1):mx(1));
	y = (mn(2):(mx(2)-mn(2))/(gridsize-1):mx(2));

	if ~oldGrid

		[X,Y] = meshgrid(x,y);
	% 	tic
	% 	ud.F = TriScatteredInterp(ud.data(:,1),ud.data(:,2),ud.data(:,3));
	% 	Z = ud.F(X,Y);
		Z = griddata(ud.data(:,1),ud.data(:,2),ud.data(:,3),X,Y); %#ok<GRIDD>
		waitbar(1);
	%	toc
	
	else
		

		method = @mean;

		xm = zeros(1,gridsize-1);
		ym = zeros(1,gridsize-1);
		Z = zeros(gridsize-1,gridsize-1);

		for i = 1:gridsize-1
			I = find(ud.data(:,1)>=x(i) & ud.data(:,1)<=x(i+1));
			xm(i) = (x(i)+x(i+1))/2;
			for j = 1:gridsize-1
				J = I(ud.data(I,2)>=y(j) & ud.data(I,2)<=y(j+1)); 
				ym(j) = (y(j)+y(j+1))/2;
				Z(j,i) = method(ud.data(J,3),1);
			end
			waitbar(i*(gridsize-1)/(gridsize-1)^2);
		end

		[X,Y] = meshgrid(xm,ym);
		
	end
	
	close(h);

end

function out = rotationMatrix(arg,units)

if (numel(arg)==3)	% calculate the rotation matrix
	if strcmpi(units,'deg'), ypr = pi*arg/180;
	else ypr = arg;
	end
	Rz = [cos(ypr(1)) -sin(ypr(1)) 0; sin(ypr(1)) cos(ypr(1)) 0; 0 0 1];
	Ry = [cos(ypr(2)) 0 sin(ypr(2)); 0 1 0; -sin(ypr(2)) 0 cos(ypr(2))];
	Rx = [1 0 0; 0 cos(ypr(3)) -sin(ypr(3)); 0 sin(ypr(3)) cos(ypr(3))];
	R = Rz*Ry*Rx;
	out = R;
else	% calculate angles from the rotation matrix
	R = arg;
	ypr = zeros(1,3);
	ypr(1) = atan2(R(2,1),R(1,1));
	ypr(2) = atan2(-R(3,1),sqrt((R(3,2)^2)/(R(3,3)^2)));
	ypr(3) = atan2(R(3,2),R(3,3));
	if strcmpi(units,'deg'), out = 180*ypr/pi;
	else out = ypr;
	end
end
end

function delim = guessdelim(str)
%GUESSDELIM Take stab at default delim for this string.

%   Copyright 1984-2002 The MathWorks, Inc. 
%   $Revision: 1.5 $  $Date: 2002/06/17 13:25:28 $

% bail if str is empty
if isempty(str)
    delim = '';
    return;
end

% count num lines
numLines = length(find(str == sprintf('\n')));

% set of column delimiters to try - ordered by quality as delim
delims = {sprintf('\t'), ',', ';', ':', '|', ' '};

% remove any delims which don't appear at all
% need to rethink based on headers and footers which are plain text
goodDelims = {};
goodDelimCounts = [];
for i = 1:length(delims)
    numDelims(i) = length(find(str == sprintf(delims{i})));
    if numDelims(i) ~= 0
        % this could be a delim
        goodDelims{end+1} = delims{i};
    end
end

% if no delims were found, return empty string
if isempty(goodDelims)
    delim = '';
    return;
end

% if the num delims is greater or equal to num lines,
% this will be the default (so return)
for i = 1:length(delims)
    delim = delims{i};
    if numDelims(i) > numLines
        return;
    end
end

% no delimiter was a clear win from above, choose the first
% in the delimiter list
delim = goodDelims{1};
end


% CALLBACK FUNCTIONS ----------------------------------------------

function btnRotate90_ClickedCallback(hObject, eventdata, handles)
ud = get(handles.figMain,'UserData');

ypr = zeros(1,3);
if (hObject==handles.btnRotateClockwise), ypr(1) = -pi/2;
elseif (hObject==handles.btnRotateAnticlockwise), ypr(1) = pi/2;
end

R = rotationMatrix(ypr,'rad');
ud.data = rotateData(ud.data,R);
[~,centr] = getMinMaxCenter(ud.data);
[ud.X,ud.Y,ud.Z] = rotateGrid(ud.X,ud.Y,ud.Z,centr,R);
ud.modified = setModified(ud.modified,1,handles,ud.fname,ud.windowName);
ud.PCs = [];
ud.gridRegenerated = 0;
set(handles.btnSelectTool,'Enable','off');
set(handles.btnSelectPolygonTool,'Enable','off');

set(handles.figMain,'UserData',ud);
updatePlots(handles);
set([handles.btnStoreChanges handles.btnResetChanges],'Enable','on');
end

function txtRot_Callback(hObject, eventdata, handles)
% hObject    handle to txtYaw (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Hints: get(hObject,'String') returns contents of txtYaw as text
%        str2double(get(hObject,'String')) returns contents of txtYaw as a double
[hSl,hTxt] = modifyRotSliders(handles,'gethandles');

posStr = get(hTxt,'String');
pos = zeros(1,numel(posStr));

for i = 1:numel(posStr)
	try
		pos(i) = round(1000*str2double(posStr{i}))/1000;
	catch
		pos(i) = 0;
	end
	if pos(i)>get(hSl(i),'Max') 
		pos(i) = get(hSl(i),'Max');
	elseif pos(i)<get(hSl(i),'Min')
		pos(i) = get(hSl(i),'Min');
	end
	set(hSl(i),'Value',pos(i));
	set(hTxt(i),'String',sprintf('%0.3f',pos(i)));
end

drawnow;
slRot_Callback(hObject, eventdata, handles);
end

function slRot_Callback(hObject, eventdata, handles)

ud = get(handles.figMain,'UserData');
if ~isfield(ud,'orgData') || isempty(ud.orgData), 
	modifyRotSliders(handles,'reset');
	return; 
end

[hSl,hTxt] = modifyRotSliders(handles,'disable');
set(handles.slGridSize,'Enable','off');

pos = round(1000*cell2mat(get(hSl,'Value')))/1000;
for i = 1:numel(hSl), set(hTxt(i),'String',sprintf('%0.3f',pos(i))); end

R = rotationMatrix(pos,'deg');

ud.data = rotateData(ud.orgData,R);
[dummy,centr] = getMinMaxCenter(ud.orgData);
[ud.X,ud.Y,ud.Z] = rotateGrid(ud.orgX,ud.orgY,ud.orgZ,centr,R);
ud.modified = setModified(ud.modified,1,handles,ud.fname,ud.windowName);
ud.PCs = [];
ud.gridRegenerated = 0;
set(handles.figMain,'UserData',ud);
updatePlots(handles);
modifyRotSliders(handles,'enable');
set(handles.slGridSize,'Enable','on');
set([handles.btnStoreChanges handles.btnResetChanges],'Enable','on');
end

function slGridSize_Callback(hObject, eventdata, handles)
% hObject    handle to slGridSize (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of sliderpos = 10*round(get(hObject,'Value')/10);
% dbstack
set(handles.slGridSize,'Enable','off');
[dummy,dummy,status] = modifyRotSliders(handles,'disable');
pos = 10*round(get(handles.slGridSize,'Value')/10);
set(handles.txtGridSize,'String',[num2str(pos) ' x ' num2str(pos)]);
set(handles.slGridSize,'Value',pos);
ud = get(handles.figMain,'UserData');
ud.gridsize = pos;
set(handles.figMain,'UserData',ud);
updatePlots(handles,true);
if strcmpi(get(handles.btnSelectTool,'State'),'on') || strcmpi(get(handles.btnSelectPolygonTool,'State'),'on')
	set(handles.axMain,'View',[0 90]); 
end

set(handles.slGridSize,'Enable','on');
if strcmpi(status,'on'), modifyRotSliders(handles,'enable'); end
end

function btnAutoRotate_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnAutoRotate (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

ud = get(handles.figMain,'UserData');
if any(any(isnan(ud.orgData)))
	choice = questdlg('NaNs have been detected in the data. The result might be unreliable. Do you want to continue?', 'Confirm operation','Yes','No','No');
	if strcmpi('No',choice)
		return
	end
end
ud.PCs = calcPCs(ud.orgData); 

% R = ud.PCs;		% not a proper rotation matrix, as det(r) = -1
% ypr = rotationMatrix(-R,'rad');
% mask = (abs(ypr)>pi/2);
% if any(mask)
% 	ypr(mask) = pi+ypr(mask);
% 	R = rotationMatrix(ypr,'rad'); 
% end
% ud.data = rotateData(ud.orgData,R);

ud.data = rotateData(ud.orgData,ud.PCs);
%ud.F = TriScatteredInterp(ud.data(:,1),ud.data(:,2),ud.data(:,3));
ud.PCs = calcPCs(ud.data); 
% calculate angles from rotation matrix
% angYaw = atan(r(2,1)/r(1,1));
% angPitch = atan(-r(3,1)/sqrt((r(3,2)^2)/(r(3,3)^2)));
% angRoll = atan(r(3,2)/r(3,3));
% angPitch2 = -asin(r(3,1));

%ud = rotateGrid(ud,ud.PCs);
%ud.X = []; ud.Y = []; ud.Z = [];
set(handles.figMain,'UserData',ud);
updatePlots(handles);
ud = get(handles.figMain,'UserData');
ud.gridRegenerated = 1;
ud.modified = setModified(ud.modified,1,handles,ud.fname,ud.windowName);
modifyRotSliders(handles,'reset');
modifyRotSliders(handles,'disable');
ud.PCs = [];
set(handles.figMain,'UserData',ud);
set([handles.btnStoreChanges handles.btnResetChanges],'Enable','on');
end

function btnResetChanges_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnResetChanges (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end

ud.data = ud.orgData;
ud.PCs = [];
ud.hl = []; ud.polyPts = [];
ud.X = ud.orgX; ud.Y = ud.orgY; ud.Z = ud.orgZ;
ud.hCropRect = [];
if strcmpi(get(handles.btnSelectTool,'State'),'off') || strcmpi(get(handles.btnSelectPolygonTool,'State'),'off')
	modifyRotSliders(handles,'reset'); 
end

set(handles.btnSelectTool,'Enable','on');
set(handles.btnSelectPolygonTool,'Enable','on');

set(handles.figMain,'UserData',ud);
updatePlots(handles);
if strcmpi(get(handles.btnSelectTool,'State'),'on') || strcmpi(get(handles.btnSelectPolygonTool,'State'),'on') || strcmpi(get(handles.btnContourCrop,'State'),'on')
	set(handles.axMain,'View',[0 90]); 
end
set([handles.btnResetChanges handles.btnStoreChanges],'Enable','off');
end

function btnResetView_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnResetView (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end

set(handles.axMain,'View',ud.viewpoints(end,:));
set(handles.axXZ,'View',ud.viewpoints(1,:));
set(handles.axYZ,'View',ud.viewpoints(2,:));
set(handles.axXY,'View',ud.viewpoints(3,:));
zoom out;
axis(handles.axMain,'equal'); axis(handles.axMain,'tight');
end

function btnShowPCs_Callback(hObject, eventdata, handles)
% hObject    handle to btnShowPCs (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Hint: get(hObject,'Value') returns toggle state of btnShowPCs
ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end
if isempty(eventdata), eventdata = handles.axMain; end

if strcmpi(get(hObject,'State'),'on'), 
	[mm,centr] = getMinMaxCenter(ud.data);
	p = getFrameCoord(mm,centr);
	if isempty(ud.PCs), ud.PCs = calcPCs(ud.data); end
	c = ones(size(p,1),1)*centr;
	p = c + (ud.PCs' * (p-c)')';
	ud.hPCs = displayFrame(ud.hPCs,1,p,{'k:',1.5},eventdata);

else
	ud.hPCs = displayFrame(ud.hPCs,0);
end
set(handles.figMain,'UserData',ud);
end

function btnShowGuides_Callback(hObject, eventdata, handles)
% hObject    handle to btnShowGuides (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Hint: get(hObject,'Value') returns toggle state of btnShowGuides
ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end
if isempty(eventdata), eventdata = [handles.axMain handles.axXZ handles.axYZ handles.axXY]; end

if strcmpi(get(hObject,'State'),'on'), 
	[mm,centr] = getMinMaxCenter(ud.data);
	p = getFrameCoord(mm,centr);
	ud.hGuides = displayFrame(ud.hGuides,1,p,{'k--',1},eventdata);
else
	ud.hGuides = displayFrame(ud.hGuides,0);
	if strcmpi(get(handles.btnShowMoreGuides,'State'),'on'),
		set(handles.btnShowMoreGuides,'State','off');
		btnShowMoreGuides_Callback(handles.btnShowMoreGuides,eventdata,handles);
	end
end
set(handles.figMain,'UserData',ud);
end

function btnShowMoreGuides_Callback(hObject, eventdata, handles)
% hObject    handle to btnShowGuides (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of btnShowGuides
ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end
if isempty(eventdata), eventdata = [handles.axMain handles.axXZ handles.axYZ handles.axXY]; end

if strcmpi(get(hObject,'State'),'on') 
	showMoreGuides(handles,eventdata,1);
	if strcmpi(get(handles.btnShowGuides,'State'),'off'),
		set(handles.btnShowGuides,'State','on');
		btnShowGuides_Callback(handles.btnShowGuides,eventdata,handles);
	end
else
	showMoreGuides(handles,[],0);
end
end

function btnStoreChanges_ClickedCallback(hObject, eventdata, handles)
ud = get(handles.figMain,'UserData');
ud.orgData = ud.data;
% ud.F = TriScatteredInterp(ud.data(:,1),ud.data(:,2),ud.data(:,3));
%ud.X = []; ud.Y = []; ud.Z = [];
set(handles.figMain,'UserData',ud);
updatePlots(handles);
ud = get(handles.figMain,'UserData');
ud.gridRegenerated = 1;
ud.orgX = ud.X; ud.orgY = ud.Y; ud.orgZ = ud.Z;
ud.PCs = [];
if strcmpi(get(handles.btnSelectTool,'State'),'off') || strcmpi(get(handles.btnSelectPolygonTool,'State'),'off')
	modifyRotSliders(handles,'reset'); 
end

if strcmpi(get(handles.btnSelectTool,'State'),'on'), set(handles.btnSelectTool,'State','off'); end
if strcmpi(get(handles.btnSelectPolygonTool,'State'),'on'),	set(handles.btnSelectPolygonTool,'State','off'); end

if strcmpi(get(handles.btnContourCrop,'State'),'on')
    set(handles.btnContourCrop,'State','off');
else
    set([handles.btnSelectTool handles.btnSelectPolygonTool],'Enable','on');
end

set([handles.btnResetChanges handles.btnStoreChanges],'Enable','off');
set(handles.figMain,'UserData',ud);
end

function btnFlip_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnFlipLeftRight (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end
[dummy,centr] = getMinMaxCenter(ud.data);
c = ones(size(ud.data,1),1)*centr;
switch(hObject)
	case handles.btnFlipLeftRight
		[ud.X,ud.Y,ud.Z] = flipGrid(ud.X,ud.Y,ud.Z,1,centr);
		ud.data(:,1) = 2*c(:,1)-ud.data(:,1);
	case handles.btnFlipBackFront
		[ud.X,ud.Y,ud.Z] = flipGrid(ud.X,ud.Y,ud.Z,2,centr);
		ud.data(:,2) = 2*c(:,2)-ud.data(:,2);
	case handles.btnFlipUpDown
		[ud.X,ud.Y,ud.Z] = flipGrid(ud.X,ud.Y,ud.Z,3,centr);
		ud.data(:,3) = 2*c(:,3)-ud.data(:,3);
end
ud.PCs = [];
ud.gridRegenerated = 0;
set(handles.figMain,'UserData',ud);
modifyRotSliders(handles,'disable');
updatePlots(handles);
set([handles.btnStoreChanges handles.btnResetChanges],'Enable','on');
end


function btnRegenGrid_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnRegenGrid (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end
ud.X = {}; ud.Y = {}; ud.Z = {}; ud.PCs = [];
ud.gridRegenerated = 1;
set(handles.figMain,'UserData',ud);
updatePlots(handles);
end

function btnOpen_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnOpen (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
menuitemOpen_Callback(hObject, eventdata, handles);
end

function btnSave_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to btnSave (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
menuitemSave_Callback(hObject, eventdata, handles);
end


function ddPlotType_Callback(hObject, eventdata, handles)
% hObject    handle to ddPlotType (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Hints: contents = cellstr(get(hObject,'String')) returns ddPlotType contents as cell array
%        contents{get(hObject,'Value')} returns selected item from ddPlotType
updatePlots(handles,false);
end

function ddColormap_Callback(hObject, eventdata, handles)
% hObject    handle to ddColormap (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns ddColormap contents as cell array
%        contents{get(hObject,'Value')} returns selected item from ddColormap
updateColormap(handles);
end

function menuitemOpen_Callback(hObject, eventdata, handles)
% hObject    handle to menuitemOpen (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

ud_old = get(handles.figMain,'UserData');
if isfield(ud_old,'modified') && (ud_old.modified==1) && strcmpi(confirmSave,'Yes')
	menuitemSave_Callback(hObject, eventdata, handles); 
end

[fname,pathname] = uigetfile({'*.asc;*.csv','All supported files'; '*.asc','ASC files'; '*.csv','CSV files'; '*.*','All files'},'Open file',ud_old.pathname);

if ~isequal(fname,0) && ~isequal(pathname,0)
	
	ud.windowName = ud_old.windowName;
	ud.viewpoints = ud_old.viewpoints;
	ud.version = ud_old.version;
	ud.axMainPos = ud_old.axMainPos;
	ud.contours = ud_old.contours;
	if isfield(ud_old,'storedViewpoint'), ud.storedViewpoint = ud_old.storedViewpoint; end
	if isfield(ud_old,'disabledCtrls'), ud.disabledCtrls = ud_old.disabledCtrls; end
	if isfield(ud_old,'storedFrameStates'), ud.storedFrameStates = ud_old.storedFrameStates; end
	
	ud.pathname = pathname;
	ud.fname = fname;
	
	% load the data
	[~,~,~,data] = loadFootImage([ud.pathname ud.fname]);
	ud.orgData = data(:,1:3);
	
% 	% load the data
% 	try
% 		% guess the delimiter
% 		fid = fopen([ud.pathname ud.fname]);
%  		str = fread(fid,4096,'*char')';
%  		fclose(fid);
%  		delimiter = guessdelim(str);
%  		if isspace(delimiter), delimiter = ''; end 
% 		
% 		% examine header row if present
% 		if isempty(regexp(str,'^\s*\*\*','once'))
% 			line = sscanf(str,'%d');
% 			if isempty(line)
% 				data = dlmread([ud.pathname ud.fname],delimiter,1);
% 			else
% 				data = dlmread([ud.pathname ud.fname],delimiter);
% 			end
% 		else
% 			str = regexp(str,'^\s*\*\*\D*\d+\D*\*\*','match');
% 			numlines = regexp(str,'\d+','match');
%  			data = dlmread([ud.pathname ud.fname],delimiter,[1 0 str2double(numlines{1}) 2]);
% 		end
% 		 
% 	catch ex
% 		try		% one more try
% 			data = importdata([ud.pathname ud.fname]);
% 			if isstruct(data), data = data.data; end
% 			data = data(:,1:3);
% 		catch ex
% 			str = sprintf('Error reading from file.\n\nException message:\n%s',ex.message);
% 			msgbox(str,'Error','error','modal');
% 			return
% 		end
% 	end
% 	ud.orgData = data(:,1:3);

	% set properties which will change with rotation
	ud.modified = 0;
	ud.data = ud.orgData;
	ud.PCs = [];
	ud.hGuides = [];
	ud.hPCs = [];
	ud.hCropRect = [];
	ud.selMode = 0;
	ud.hl = [];
	ud.polyPts = [];

	% update GUI elements
	set(handles.figMain,'Name',[ud.windowName ' - ' ud.fname]);
	modifyRotSliders(handles,'reset');
	set(handles.btnSelectTool,'State','off');
	set(handles.btnSelectPolygonTool,'State','off');
	t = sort(data(:,3)); mn = t(3);
    set(handles.slContourCrop,'max',max(ud.data(:,3)),'min',mn,'Value',max(ud.data(:,3)));
		
	% generate grid for displaying
	g = get(handles.slGridSize,'Value');
	[ud.X,ud.Y,ud.Z] = generateGrid(g,ud,strcmpi(get(handles.btnOldGrid,'State'),'on'));
	ud.orgX = ud.X; ud.orgY = ud.Y; ud.orgZ = ud.Z;
	ud.gridRegenerated = 1;
	set(handles.axMain,'Position',ud.axMainPos);
	set(handles.figMain,'UserData',ud);
	updatePlots(handles);
	
	% enable UI controls
	hUICtrls = [handles.btnSave handles.btnZoomIn handles.btnZoomOut handles.btnPan ...
		handles.btnRotate handles.btnResetView handles.btnAutoRotate handles.btnRegenGrid ...
		handles.btnFlipUpDown handles.btnFlipLeftRight handles.btnFlipBackFront ...
		handles.btnRotateClockwise handles.btnRotateAnticlockwise handles.btnSelectTool ...
		handles.btnSelectPolygonTool handles.btnContour handles.btnZeroNan handles.btnContourCrop ...
		handles.btnInterpError handles.btnExportView];
	set(hUICtrls,'Enable','on');
	
end
end

function menuitemSave_Callback(hObject, eventdata, handles)
% hObject    handle to menuitemSave (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

ud = get(handles.figMain,'UserData');
if ~isfield(ud,'data') || isempty(ud.data), return; end

% h.f = figure('NumberTitle','off','Name','Save options','units','pixels','position',[200,200,200,100],'toolbar','none','menu','none','Visible','off','WindowStyle','modal');
h.f = figure('NumberTitle','off','Name','Save options','units','pixels','position',[200,200,200,140],'Visible','off');
centerFigure(h.f);
b = 0;

if ~isfield(ud,'landmarkPts'), ud.landmarkPts = []; end
landmarks = cell(size(ud.landmarkPts,1),1);
for i = 1:numel(landmarks)
    landmarks{i} = sprintf('L%d: %0.1f, %0.1f',i,ud.landmarkPts(i,1:2));
end

h.c(1) = uicontrol('style','checkbox',  'units','pixels','position',[10,120+b,180,15],'string','Discard NaNs');
h.c(2) = uicontrol('style','checkbox',  'units','pixels','position',[10,100+b,180,15],'string','Center XY');    
h.c(3) = uicontrol('style','checkbox',  'units','pixels','position',[10,080+b,180,15],'string','Normalise Z');    
h.c(4) = uicontrol('style','checkbox',  'units','pixels','position',[10,060+b,180,15],'string','Resample from grid');
h.c(5) = uicontrol('style','popupmenu', 'units','pixels','position',[10,040+b,180,15],'string',['Origin at landmark';landmarks]);
h.p    = uicontrol('style','pushbutton','units','pixels','position',[65,010+b,80,20] ,'string','OK','callback',@p_call);
set(h.f,'DeleteFcn',@p_call);
set(h.f ,'WindowStyle','modal','Visible','on');
drawnow;
checked = [];
uiwait(h.f);

% Pushbutton/window close callback
function p_call(varargin)
	vals = get(h.c,'Value');
	checked = [vals{:}];
	if ishandle(h.f), delete(h.f); end
end

data = ud.data;

%resample from grid
if checked(4)
	data = [ud.X(:),ud.Y(:),ud.Z(:)];
end

% discard NaNs
if checked(1)
	mask = ~isnan(data(:,3));
	data = data(mask,:);
end

% normalise XY
if checked(2)
    mn = min(data(:,1:2));
	data(:,1:2) = data(:,1:2) - ones(size(data,1),1)*mn;
end

% normalise Z
if checked(3)
    mn = min(data(:,3));
    mx = max(data(:,3));
    data(:,3) = (data(:,3)-mn)/(mx-mn);
end

% origin at landmark
checked(5) = checked(5)-1;
if checked(5)
    origin = points2real(data,ud.landmarkPts(checked(5),1:2));
    data = data-ones(size(data,1),1)*origin;
end


filter = {'*.asc','ASC files'; '*.csv','CSV files'};
if strcmpi(ud.fname(end-3:end),'.csv'), filter = flipud(filter); end
[fname,pathname] = uiputfile(filter,'Save file',ud.pathname);

if ~isequal(fname,0) && ~isequal(pathname,0)

	if strcmpi(fname(end-3:end),'.asc')
		delim = ' ';
		dlmwrite([pathname fname],data,delim);
	elseif strcmpi(fname(end-3:end),'.csv'), 
		delim = ',';
		fid = fopen([pathname fname],'w');
		fwrite(fid,sprintf('X,Y,Z\n'),'char');
 		fclose(fid);
 		dlmwrite([pathname fname],data,'delimiter',delim,'-append');
	else
		return;
	end
	ud.pathname = pathname;
	ud.fname = fname;
	ud.modified = setModified(ud.modified,0,handles,ud.fname,ud.windowName);

	ud.orgData = ud.data;
	ud.orgX = ud.X; ud.orgY = ud.Y; ud.orgZ = ud.Z;
	ud.PCs = [];
	modifyRotSliders(handles,'reset');

	set(handles.figMain,'UserData',ud);

end
end

function menuitemExit_Callback(hObject, eventdata, handles)
% hObject    handle to menuitemExit (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
	close(handles.figMain);
end

function menuitemAbout_Callback(hObject, eventdata, handles)
% hObject    handle to menuitemAbout (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
ud = get(handles.figMain,'UserData');
str = ud.windowName;
for i = 1:numel(ud.info), str = [str sprintf('\n%s',ud.info{i})]; end
msgbox(str,'About','help','modal');
end


function btnSelectTool_OnCallback(hObject, eventdata, handles)

	% disable other UI controls
	ud = get(handles.figMain,'UserData');
	ud.disabledCtrls = [handles.btnAutoRotate handles.btnRegenGrid handles.btnFlipUpDown ...
		handles.btnFlipLeftRight handles.btnFlipBackFront handles.btnRotateClockwise ...
		handles.btnRotateAnticlockwise handles.btnShowGuides handles.btnShowMoreGuides ...
		handles.btnShowPCs handles.ddPlotType handles.slYaw handles.slPitch handles.slRoll ...
		handles.txtYaw handles.txtPitch handles.txtRoll handles.btnResetView handles.btnSelectPolygonTool ...
		handles.btnRotate handles.btnZeroNan handles.btnContour handles.btnExportView];
	set(ud.disabledCtrls,'Enable','off');

	if strcmpi(get(handles.btnRotate,'State'),'on')
		set(handles.btnRotate,'State','off');
		rotate3d off
	end

	ud.storedViewpoint = get(handles.axMain,'View');
	ud.storedFrameStates = get([handles.btnShowGuides handles.btnShowPCs],'State');
	set(handles.axMain,'View',[0 90]);

	set([handles.btnShowGuides handles.btnShowMoreGuides handles.btnShowPCs],'State','off');
 	ud.hGuides = []; ud.hMoreGuides = []; ud.PCs = [];
	set(handles.figMain,'UserData',ud);

end

function btnSelectTool_OffCallback(hObject, eventdata, handles)
	
	ud = get(handles.figMain,'UserData');
	if isfield(ud,'storedViewpoint') && ~isempty(ud.storedViewpoint)
		set(handles.axMain,'View',ud.storedViewpoint);
		ud.storedViewpoint = [];
	end
	if isfield(ud,'hCropRect') && ~isempty(ud.hCropRect)
		if ishandle(ud.hCropRect), delete(ud.hCropRect); end
		ud.hCropRect = [];
	end
	if isfield(ud,'disabledCtrls') && ~isempty(ud.disabledCtrls)
		set(ud.disabledCtrls,'Enable','on');
		ud.disabledCtrls = [];
	end
	set(handles.figMain,'UserData',ud);
	set(handles.btnCrop,'Enable','off');
	set(handles.figMain,'WindowButtonMotionFcn',[]);
	if isfield(ud,'storedFrameStates') && ~isempty(ud.storedFrameStates)
		set(handles.btnShowGuides,'State',ud.storedFrameStates{1});
		set(handles.btnShowPCs,'State',ud.storedFrameStates{2});
	end
	
end


function [hit,cp] = axHittest(cp,ax)
	xl = get(ax,'XLim');
	yl = get(ax,'YLim');

	if(cp(1,1)>=xl(1) && cp(1,1)<=xl(2) && cp(1,2)>=yl(1) && cp(1,2)<=yl(2))
		hit = 1;
	else
		hit = 0;
		cp(1,1) = min(max(cp(1,1),xl(1)),xl(2));
		cp(1,2) = min(max(cp(1,2),yl(1)),yl(2));
	end
	cp = cp(1,1:2);
end


function figMain_WindowButtonDownFcn(hObject, eventdata, handles)

	if strcmpi(get(handles.btnSelectTool,'State'),'off'), return; end
	ud = get(handles.figMain,'UserData');

	% see if the button was clicked within  axMain
	cp = get(handles.axMain,'CurrentPoint');
	if axHittest(cp,handles.axMain)
		curPoint = get(handles.axMain,'CurrentPoint');
		if isfield(ud,'hCropRect') && ~isempty(ud.hCropRect)
			cp = vertexpicker(ud.hMainPlot,curPoint);
			for i = 1:numel(ud.hCropRect)
				xdata = get(ud.hCropRect(i),'Xdata');
				ydata = get(ud.hCropRect(i),'Ydata');
				if all(xdata==cp(1)) || all(ydata==cp(2))
					set(ud.hCropRect(i),'LineStyle',':'); 
					set(handles.figMain,'WindowButtonMotionFcn',@(hObject,eventdata)footprocessor('dragRect',i,eventdata,guidata(hObject)));
					return
				end
			end
			
			if ishandle(ud.hCropRect), delete(ud.hCropRect); end
			ud.hCropRect = [];
		end
		ud.orgUnits = get(handles.axMain,'Units');
		set(handles.axMain,'Units','pixels');
		ud.selMode = 1;
		ud.startPoint = curPoint;
		rbbox();
		set(handles.figMain,'UserData',ud);
	end
end

function figMain_WindowButtonUpFcn(hObject, eventdata, handles)

	if strcmpi(get(handles.btnSelectTool,'State'),'off'), return; end
	ud = get(handles.figMain,'UserData');

	if ~isempty(get(handles.figMain,'WindowButtonMotionFcn'))

		set(handles.figMain,'WindowButtonMotionFcn',@(hObject,eventdata)footprocessor('trackRect',hObject,eventdata,guidata(hObject)));

	elseif isfield(ud,'selMode') && (ud.selMode==1)

		ud.endPoint = get(handles.axMain,'CurrentPoint');
		vStart = vertexpicker(ud.hMainPlot,ud.startPoint);
		vEnd = vertexpicker(ud.hMainPlot,ud.endPoint);

		if ~isempty(vEnd)
			data = get(ud.hMainPlot,'zdata');
			if iscell(data), data = data{1}; end % contour plot
			ud.zMax = max(data(:));
			ud.xStart = vStart(1); ud.xEnd = vEnd(1);
			ud.yStart = vStart(2); ud.yEnd = vEnd(2);

			ud.hCropRect = plotRect(ud.hCropRect,handles.axMain,ud.xStart,ud.yStart,ud.xEnd,ud.yEnd,ud.zMax);

			ud.selMode = 0;
			set(handles.btnCrop,'Enable','on');
			set(handles.axMain,'Units',ud.orgUnits);
			set(handles.figMain,'UserData',ud);
			set(handles.figMain,'WindowButtonMotionFcn',@(hObject,eventdata)footprocessor('trackRect',hObject,eventdata,guidata(hObject)));
		end

	end
end

function h = plotRect(h,hAx,xStart,yStart,xEnd,yEnd,zMax)
if ~isempty(h) && ishandle(h), delete(h);
else h = zeros(1,4);
end
hold(hAx,'on');
h(1) = plot3(hAx,[xStart xStart],[yStart yEnd],[zMax zMax],'LineWidth',2);
h(2) = plot3(hAx,[xEnd xEnd],[yStart yEnd],[zMax zMax],'LineWidth',2);
h(3) = plot3(hAx,[xStart xEnd],[yStart yStart],[zMax zMax],'LineWidth',2);
h(4) = plot3(hAx,[xStart xEnd],[yEnd yEnd],[zMax zMax],'LineWidth',2);
hold(hAx,'off');
end
% drawnow;

function trackRect(hObject, eventdata, handles)
	ud = get(handles.figMain,'UserData');
	if ~isfield(ud,'hCropRect') || isempty(ud.hCropRect), set(handles.figMain,'WindowButtonMotionFcn',[]); end
	curPoint = vertexpicker(ud.hMainPlot,get(handles.axMain,'CurrentPoint'));
	if isempty(curPoint), return; end
	for i = 1:numel(ud.hCropRect)
		xdata = get(ud.hCropRect(i),'Xdata');
		ydata = get(ud.hCropRect(i),'Ydata');
		if all(xdata==curPoint(1)) || all(ydata==curPoint(2))
			set(ud.hCropRect(i),'LineStyle','--');
		else
			set(ud.hCropRect(i),'LineStyle','-');
		end
	end
end

function dragRect(hObject, eventdata, handles)

	ud = get(handles.figMain,'UserData');
	curPoint = get(handles.axMain,'CurrentPoint');
	cp = vertexpicker(ud.hMainPlot,curPoint);
	if isempty(cp), return; end

	x = get(ud.hCropRect(hObject),'Xdata');
	y = get(ud.hCropRect(hObject),'Ydata');

	if x(1)==x(2)	% vertical edge
		if (ud.xStart==x(1)), ud.xStart = cp(1);
		else ud.xEnd = cp(1);
		end
	elseif y(1)==y(2)	% horizontal edge
		if (ud.yStart==y(1)), ud.yStart = cp(2);
		else ud.yEnd = cp(2);
		end
	end
	ud.hCropRect = plotRect(ud.hCropRect,handles.axMain,ud.xStart,ud.yStart,ud.xEnd,ud.yEnd,ud.zMax);
	set(handles.figMain,'UserData',ud);
end


function btnSelectPolygonTool_OnCallback(hObject, eventdata, handles)
	% disable other UI controls
	ud = get(handles.figMain,'UserData');
	
	ud.disabledCtrls = [handles.btnAutoRotate handles.btnRegenGrid handles.btnFlipUpDown ...
		handles.btnFlipLeftRight handles.btnFlipBackFront handles.btnRotateClockwise ...
		handles.btnRotateAnticlockwise handles.btnShowGuides handles.btnShowMoreGuides ...
		handles.btnShowPCs handles.ddPlotType handles.slYaw handles.slPitch handles.slRoll ...
		handles.txtYaw handles.txtPitch handles.txtRoll handles.btnResetView handles.btnSelectTool ...
		handles.btnRotate handles.btnZeroNan handles.btnContour handles.btnExportView];
	set(ud.disabledCtrls,'Enable','off');
	
	if strcmpi(get(handles.btnRotate,'State'),'on')
		set(handles.btnRotate,'State','off');
		rotate3d off
	end

	ud.storedViewpoint = get(handles.axMain,'View');
	ud.storedFrameStates = get([handles.btnShowGuides handles.btnShowPCs],'State');
	set(handles.axMain,'View',[0 90]);

	set([handles.btnShowGuides handles.btnShowMoreGuides handles.btnShowPCs],'State','off');
 	ud.hGuides = []; ud.hMoreGuides = []; ud.PCs = [];
	set(handles.figMain,'UserData',ud);

	set(handles.figMain,'pointer','circle');
	set(handles.figMain,'WindowButtonDownFcn',@(hObject, eventdata) wbdPolygon(hObject, eventdata, handles));
	set(handles.axMain,'DrawMode','fast');
end

function btnSelectPolygonTool_OffCallback(hObject, eventdata, handles)
	ud = get(handles.figMain,'UserData');
	if isfield(ud,'storedViewpoint') && ~isempty(ud.storedViewpoint)
		set(handles.axMain,'View',ud.storedViewpoint);
		ud.storedViewpoint = [];
	end
	if isfield(ud,'hl') && ~isempty(ud.hl)
		if ishandle(ud.hl), delete(ud.hl); end
		ud.hl = [];
	end
	ud.polyPts = [];
	if isfield(ud,'disabledCtrls') && ~isempty(ud.disabledCtrls)
		set(ud.disabledCtrls,'Enable','on');
		ud.disabledCtrls = [];
	end
	set(handles.figMain,'UserData',ud);
	set(handles.btnCrop,'Enable','off');
	set(handles.figMain,'WindowButtonMotionFcn',[]);
	if isfield(ud,'storedFrameStates') && ~isempty(ud.storedFrameStates)
		set(handles.btnShowGuides,'State',ud.storedFrameStates{1});
		set(handles.btnShowPCs,'State',ud.storedFrameStates{2});
	end

	set(handles.figMain,'WindowButtonDownFcn',@(hObject, eventdata) figMain_WindowButtonDownFcn(hObject, eventdata, handles));
	set(handles.figMain,'WindowButtonUpFcn',@(hObject, eventdata) figMain_WindowButtonUpFcn(hObject, eventdata, handles));
	set(handles.axMain,'DrawMode','normal');
	set(handles.figMain,'Pointer','arrow')

end

function wbdPolygon(hObject, eventdata, handles)

	cp = get(handles.axMain,'CurrentPoint');
	if ~axHittest(cp,handles.axMain), return, end

	% left click
	if strcmp(get(hObject,'SelectionType'),'normal')
		ud = get(handles.figMain,'UserData');

		% first point
		if ~isfield(ud,'polyPts') || isempty(ud.polyPts)
			data = get(ud.hMainPlot,'zdata');
			if iscell(data), data = data{1}; end % contour returns a cell 
			ud.zMax = max(data(:));
			ud.polyPts = [];
			ud.hl = [];
			ud.hMarker = [];
		end

		ud.polyPts = [ud.polyPts; cp(1,1:2)];

		xinit = cp(1,1); yinit = cp(1,2); zinit = ud.zMax;
 		ud.hl(end+1) = line('XData',xinit,'YData',yinit,'ZData',zinit,'Marker','.','MarkerSize',20,'color','b','LineWidth',2);
		set(handles.figMain,'UserData',ud);

		set(hObject,'WindowButtonMotionFcn',@(hObject, eventdata) wbmPolygon(hObject, eventdata, handles));
		set(hObject,'WindowButtonUpFcn',@(hObject, eventdata) wbuPolygon(hObject, eventdata, handles));
		
	end
	
	function wbmPolygon(hObject, eventdata, handles)

		cp = get(handles.axMain,'CurrentPoint');
		if ~axHittest(cp,handles.axMain), return, end

		ud = get(handles.figMain,'UserData');
		
		Iall = intersections(ud.polyPts,cp);
		
		% snap to the closest intersection point
		if ~isempty(Iall)
	 		curLine = [ud.polyPts(end,:); cp(1,1:2)];
			dist = sum((ones(size(Iall,1),1)*curLine(1,:) - Iall).^2,2);
			[~,minIdx] = min(dist);
			cp(1,1) = Iall(minIdx,1);
			cp(1,2) = Iall(minIdx,2);
		end
		
		xdat = [xinit cp(1,1)];
		ydat = [yinit cp(1,2)];
		zdat = [zinit ud.zMax];
		set(ud.hl(end),'XData',xdat,'YData',ydat,'ZData',zdat);
		set(handles.figMain,'UserData',ud);
		drawnow;
		
	end
		
	function wbuPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		% right click
		if strcmp(get(hObject,'SelectionType'),'alt') && size(ud.polyPts,1)>2 && isempty(intersections(ud.polyPts,ud.polyPts(1,:)))

			set(ud.hl(end),'XData',[ud.polyPts(end,1) ud.polyPts(1,1)],'YData',[ud.polyPts(end,2) ud.polyPts(1,2)],'ZData',[ud.zMax ud.zMax]);
			drawnow;

			% convert polyPts to closest real points
			ud.polyPts = points2real(ud.data,ud.polyPts); ud.polyPts = ud.polyPts(:,1:2);

			ud.xStart = min(ud.polyPts(:,1));
			ud.xEnd = max(ud.polyPts(:,1));
			ud.yStart = min(ud.polyPts(:,2));
			ud.yEnd = max(ud.polyPts(:,2));

			set(handles.figMain,'UserData',ud);
			
			set(handles.btnCrop,'Enable','on');
			set(hObject,'WindowButtonUpFcn',[]);
			set(hObject,'WindowButtonMotionFcn',@(hObject, eventdata) wbmTrackPolygon(hObject, eventdata, handles));
			set(hObject,'WindowButtonDownFcn',[]);
 			set(handles.figMain,'Pointer','arrow');
 			%set(handles.axMain,'DrawMode','normal');
			
		end
	end

	function wbmTrackPolygon(hObject, eventdata, handles)
		cp = get(handles.axMain,'CurrentPoint');
		
		% hoover tolerance
		xDiff = diff(get(handles.axMain,'XLim'));
		yDiff = diff(get(handles.axMain,'YLim'));
		xTol = xDiff/100;
		yTol = yDiff/100;
		
		ud = get(handles.figMain,'UserData');
		if ~isfield(ud,'hMarker') || isempty(ud.hMarker), ud.hMarker = nan(1,size(ud.polyPts,1)); end
		if ~isfield(ud,'hMarkerE'), ud.hMarkerE = []; end
		
		if ~isempty(ud.polyPts), polyPts = [ud.polyPts; ud.polyPts(1,:)]; 
		else polyPts = [];
		end
		A = nan(1,size(polyPts,1)-1); B = nan(1,size(polyPts,1)-1); C = nan(1,size(polyPts,1)-1);
		
		for i = 1:size(ud.polyPts,1)
 			if isnan(C(i)),	[A(i),B(i),C(i)] = lineThruPts(polyPts(i,:),polyPts(i+1,:)); end
			
			% higlight vertix on mouse hoover
			if abs(ud.polyPts(i,1)-cp(1,1))<xTol && abs(ud.polyPts(i,2)-cp(1,2))<yTol && isnan(ud.hMarker(i))
				%sqrt(sum(ud.polyPts(i,:)-cp(1,1:2)).^2)<sqrt(sum([xTol yTol].^2)) && isnan(ud.hMarker(i))
				
				if ~isempty(ud.hMarkerE), delete(ud.hMarkerE); ud.hMarkerE = []; end
				hold(handles.axMain,'on');
				ud.hMarker(i) = plot3(handles.axMain,ud.polyPts(i,1),ud.polyPts(i,2),ud.zMax,'r.','MarkerSize',25);
				hold(handles.axMain,'off');
				set(hObject,'WindowButtonDownFcn',@(hObject, eventdata) wbdDragPolygon(hObject, eventdata, handles));
				set(hObject,'WindowButtonUpFcn',@(hObject, eventdata) wbuDragPolygon(hObject, eventdata, handles));
				ud.currVert = i;
				break;
			
			% highlight edge on mouse hoover
			elseif	abs(A(i)*cp(1,1)+B(i)*cp(1,2)+C(i))/sqrt(A(i).^2+B(i).^2) < sqrt(xTol.^2+yTol.^2) && ...					% distance from the line
					cp(1,1)>(min(polyPts(i,1),polyPts(i+1,1))-xTol) && cp(1,1)<(max(polyPts(i,1),polyPts(i+1,1))+xTol) && ...	% rectangle check
 					cp(1,2)>(min(polyPts(i,2),polyPts(i+1,2))-yTol) && cp(1,2)<(max(polyPts(i,2),polyPts(i+1,2))+yTol) && ...	% rectangle check
 					sum((polyPts(i,:)-cp(1,1:2)).^2) > (xTol^2+yTol^2) && sum((polyPts(i+1,:)-cp(1,1:2)).^2) > (xTol^2+yTol^2) && ...% distance from vertexes
					all(isnan(ud.hMarker))
 				
				y = cp(1,2);
				if B(i)==0 % vertical line
					x = polyPts(i,1);
				elseif A(i)==0 || abs(atan(-A(i)/B(i))*180/pi) < 1 % (near) horizontal line
					x = cp(1,1);
					y = polyPts(i,2);
				else % other line
					x = -(B(i)*y+C(i))/A(i);
				end
				if abs(x-cp(1,1))<xTol
					delete(ud.hMarkerE);
					hold(handles.axMain,'on');
					ud.hMarkerE = plot3(handles.axMain,x,y,ud.zMax,'.b','MarkerSize',25);
					hold(handles.axMain,'off');
				end
				set(hObject,'WindowButtonDownFcn',@(hObject, eventdata) wbdAddVertex(hObject, eventdata, handles,x,y,i));
				break;
				
			else
			
				mask = ~isnan(ud.hMarker);
				delete([ud.hMarker(mask) ud.hMarkerE]);
				ud.hMarker(mask) = nan;
				ud.hMarkerE = [];
				set(hObject,'WindowButtonDownFcn','');
				set(hObject,'WindowButtonUpFcn','');
				
			end
		end
		
		drawnow;
		set(handles.figMain,'UserData',ud);
	
	end

	function wbdAddVertex(hObject, eventdata, handles, x, y, i)
		ud = get(handles.figMain,'UserData');
		if isempty(ud.hMarkerE), return; end
		ud.polyPts = [ud.polyPts(1:i,:); [x y]; ud.polyPts(i+1:end,:)];
 		ud.hMarker = [ud.hMarker(1:i) nan ud.hMarker(i+1:end)];
		ud.hl = [ud.hl(1:i) nan ud.hl(i+1:end)];
		polyPts = [ud.polyPts; ud.polyPts(1,:)];
		set(ud.hl(i),'XData',[polyPts(i,1) x],'YData',[polyPts(i,2) y],'ZData',[ud.zMax ud.zMax]);
 		ud.hl(i+1) = line('XData',[x polyPts(i+2,1)],'YData',[y polyPts(i+2,2)],'ZData',[ud.zMax ud.zMax],'Marker','.','MarkerSize',20,'color','b','LineWidth',2);
		set(handles.figMain,'UserData',ud);
	end

	function wbdDragPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		ud.wbm = get(hObject,'WindowButtonMotionFcn');
		set(hObject,'WindowButtonMotionFcn',@(hObject, eventdata) wbmDragPolygon(hObject, eventdata, handles));
		set(handles.figMain,'UserData',ud);
	end

	function wbuDragPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		set(hObject,'WindowButtonDownFcn','');
		set(hObject,'WindowButtonMotionFcn',ud.wbm);
	end

	function wbmDragPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		cp = get(handles.axMain,'CurrentPoint');

		i1 = ud.currVert;
		i2 = ud.currVert-1;
		if i2==0, i2 = numel(ud.hl); end
			
		XData = get(ud.hl(i1),'XData');
		YData = get(ud.hl(i1),'YData');
		XData(1,1) = cp(1,1);
		YData(1,1) = cp(1,2);
		set(ud.hl(i1),'XData',XData,'YData',YData);
		ud.polyPts(i1,1:2) = cp(1,1:2);
		
		XData = get(ud.hl(i2),'XData');
		YData = get(ud.hl(i2),'YData');
		XData(1,2) = cp(1,1);
		YData(1,2) = cp(1,2);
		set(ud.hl(i2),'XData',XData,'YData',YData);
		ud.polyPts(i1,1:2) = cp(1,1:2);
		
		set(ud.hMarker(i1),'XData',cp(1,1),'YData',cp(1,2));

		set(handles.figMain,'UserData',ud);
	end

	function Iall = intersections(polyPts,cp)
		Iall = []; return
		
	 	% check if current line does not intersect with other lines
		% http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
		curLine = [polyPts(end,:); cp(1,1:2)];
		A = curLine(1,:); B = curLine(2,:);
		Iall = [];
		for i = 1:size(polyPts,1)-1
			tempLine = [polyPts(i,:); polyPts(i+1,:)];
			C = tempLine(1,:); D = tempLine(2,:);
			Iall = [Iall; intersectPts(A,B,C,D)];
		end
		
	end

end

function realPts = points2real(data,pts)
	
	% convert points to closest real points
	A = data(:,1:2);
	B = pts(:,1:2);
	dist = ((B.*B)*ones(size(B,2),size(A,1)) - 2*B*A' + ones(size(B,1),size(A,2))*(A'.*A'));
	[~,I] = sort(dist,2);

	realPts = data(I(:,1),:);
end

function [A,B,C] = lineThruPts(p1,p2)

	C = 1;
	t = (p1(2)-p2(2))/(p1(1)-p2(1));
	B = -C/(p2(2)-p2(1)*t);
	A = -B*t;

end

function Iall = intersectPts(A,B,C,D)
	
	%line through AB

	Iall = [];

	E = B-A;
	F = D-C;
	P = [-E(2);E(1)];
	h = ((A-C)*P)/(F*P);

	% calculate the intersection point
	if h>0 && h<1
		I = C + F*h;
		if ((I(1)>=C(1) && I(1)<=D(1)) || (I(1)<=C(1) && I(1)>=D(1))) && ((I(2)>=C(2) && I(2)<=D(2)) || (I(2)<=C(2) && I(2)>=D(2))) &&...
		   ((I(1)>=A(1) && I(1)<=B(1)) || (I(1)<=A(1) && I(1)>=B(1))) && ((I(2)>=A(2) && I(2)<=B(2)) || (I(2)<=A(2) && I(2)>=B(2)))
			Iall = [Iall; I];
		end
	end
end

function btnCrop_ClickedCallback(hObject, eventdata, handles)

%profile on
helper(hObject, eventdata, handles)
%profile viewer

function helper(hObject, eventdata, handles)

	ud = get(handles.figMain,'UserData');
	if ~isfield(ud,'xStart') || isempty(ud.xStart), return; end

	mask = (ud.data(:,1)<=max(ud.xStart,ud.xEnd)) & (ud.data(:,1)>=min(ud.xStart,ud.xEnd)) ...
			& (ud.data(:,2)<=max(ud.yStart,ud.yEnd)) & (ud.data(:,2)>=min(ud.yStart,ud.yEnd));

	ud.data = ud.data(mask,:);
	%ud.X = [];
	if isfield(ud,'hCropRect') && ~isempty(ud.hCropRect)
		if ishandle(ud.hCropRect), delete(ud.hCropRect); end
		ud.hCropRect = [];
	end
	
	% remove everything outside the polygon (http://alienryderflex.com/polygon_fill/)
	if isfield(ud,'polyPts') && ~isempty(ud.polyPts)
	
		h = waitbar(0,'Cropping. Please wait...','Visible','off');	%,'WindowStyle','modal'); 
		centerFigure(h); set(h,'Visible','on');

		polyPts = [ud.polyPts; ud.polyPts(1,:)];

		% generate equations of lines for each polygon edge
		A = zeros(1,size(polyPts,1)-1); B = zeros(1,size(polyPts,1)-1); C = zeros(1,size(polyPts,1)-1);
		minX = zeros(1,size(polyPts,1)-1); maxX = zeros(1,size(polyPts,1)-1);
		minY = zeros(1,size(polyPts,1)-1); maxY = zeros(1,size(polyPts,1)-1);
		for i = 1:size(polyPts,1)-1
			[A(i),B(i),C(i)] = lineThruPts(polyPts(i,:),polyPts(i+1,:));
			minX(i) = min(polyPts(i,1),polyPts(i+1,1));
			maxX(i) = max(polyPts(i,1),polyPts(i+1,1));
			minY(i) = min(polyPts(i,2),polyPts(i+1,2));
			maxY(i) = max(polyPts(i,2),polyPts(i+1,2));
		end
		
		% scan-line algorithm
		maskLeave = false(size(ud.data,1),1);
		yUnique = unique(ud.data(:,2))';

		cnt = 0;
		step = round(numel(yUnique)/100);
		for y = yUnique
			cnt = cnt+1;
			if mod(cnt,step)==0 || cnt==numel(yUnique)
				waitbar(cnt/numel(yUnique)); 
			end

			maskY = (ud.data(:,2)==y);
			idxY = find(maskY);

			% find intersection points
			xInter = [];
			for i = 1:size(polyPts,1)-1
				
				% check if scanline intersects the edge
				if y<minY(i) || y>maxY(i), continue, end
				
				% check if scanline passes through a vertex (if min or max - count it twice, otherwise count it once)
				if y==polyPts(i,2) && y==polyPts(i+1,2)  % horizontal line
					if min(polyPts(:,1))==minX(i), % leftmost vertex of the polygon
						xInter(xInter==minX(i)) = [];
						xInter = [xInter minX(i)]; 
					elseif max(polyPts(:,1))==maxX(i), % rightmost vertex of the polygon
						xInter(xInter==maxX(i)) = [];
						xInter = [xInter maxX(i)]; 
					else % somewhere in the middle
						xInter(xInter==minX(i) || xInter==maxX(i)) = [];
						xInter = [xInter minX(i) minX(i) maxX(i) maxX(i)];	
					end
				
				elseif y==polyPts(i,2) && ~any(xInter == polyPts(i,1))
					xInter(end+1) = polyPts(i,1);
					j = i-1;
					if j==0, j = size(polyPts,1)-1; end
					if (y<polyPts(j,2) && y<polyPts(i+1,2)) || (y>polyPts(j,2) && y>polyPts(i+1,2))
						xInter(end+1) = xInter(end);
					end
					
				elseif y==polyPts(i+1,2) && ~any(xInter == polyPts(i+1,1))
					xInter(end+1) = polyPts(i+1,1);
					j = i+2;
					if j>size(polyPts,1), j = 2; end
% 				delete(h);
% 				hold(handles.axMain,'on');
% 				h = plot3(xInter(end),y,ud.zMax,'.r','markersize',20);
% 				hold(handles.axMain,'off');
					if (y<polyPts(i,2) && y<polyPts(j,2)) || (y>polyPts(i,2) && y>polyPts(j,2))
						xInter(end+1) = xInter(end);
					end
					
				else
					if B(i)==0 % vertical line
						xInter(end+1) = polyPts(i,1);
					else % other line
						x = -(B(i)*y+C(i))/A(i);
						if x>minX(i) && x<maxX(i), xInter(end+1) = x; end
					end
				end
			end
			
			if ~isempty(xInter)
				x = sort(xInter);
				t = ud.data(maskY,1);
 				for i = 1:floor(numel(x)/2)
 					idxX = idxY(t>=x(2*(i-1)+1) & t<=x(2*(i-1)+2));
					maskLeave(idxX) = true;
  				end
			end
		end
% 			ud.data(~maskLeave,:) = [];
		if strcmpi(get(handles.btnZeroNan','State'),'on'), ud.data(~maskLeave,3) = 0;
		else ud.data(~maskLeave,3) = nan;
		end
		
		set(handles.figMain,'pointer','circle');
		set(handles.figMain,'WindowButtonDownFcn',@(hObject, eventdata) wbdPolygon(hObject, eventdata, handles));
		set(handles.axMain,'DrawMode','fast');
		ud.polyPts = [];
		delete(h);
	end

	if isfield(ud,'hl') && ~isempty(ud.hl)
		delete(ud.hl);
		ud.hl = [];
	end
	
	ud.modified = setModified(ud.modified,1,handles,ud.fname,ud.windowName);
	set(handles.figMain,'UserData',ud);
	updatePlots(handles);
	set(handles.axMain,'View',[0 90]);
	set([handles.btnStoreChanges handles.btnResetChanges],'Enable','on');
	set(handles.btnCrop,'Enable','off');
	
end

end

function btnZeroNan_OffCallback(hObject, eventdata, handles)
	ud = get(handles.figMain,'UserData');
	mask = (ud.data(:,3)==0);
	if any(mask)
		ud.data(mask,3) = nan;
		%ud.X = [];
		set(handles.figMain,'UserData',ud);
		updatePlots(handles);
	end
end

function btnZeroNan_OnCallback(hObject, eventdata, handles)
	ud = get(handles.figMain,'UserData');
	mask = isnan(ud.data(:,3));
	if any(mask)
		ud.data(mask,3) = 0;
		%ud.X = [];
		set(handles.figMain,'UserData',ud);
		updatePlots(handles);
	end
end


function btnContour_OnCallback(hObject, eventdata, handles)
% hObject    handle to btnContour (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
	% disable other UI controls
	
	ud = get(handles.figMain,'UserData');
	
	ud.disabledCtrls = [handles.btnAutoRotate handles.btnRegenGrid handles.btnFlipUpDown ...
		handles.btnFlipLeftRight handles.btnFlipBackFront handles.btnRotateClockwise ...
		handles.btnRotateAnticlockwise handles.btnShowGuides handles.btnShowMoreGuides ...
		handles.btnShowPCs handles.ddPlotType handles.slYaw handles.slPitch handles.slRoll ...
		handles.txtYaw handles.txtPitch handles.txtRoll handles.btnResetView handles.btnSelectTool ...
		handles.btnRotate handles.btnZeroNan handles.btnSelectPolygonTool handles.btnContourCrop handles.btnExportView];
	set(ud.disabledCtrls,'Enable','off');
	
	if strcmpi(get(handles.btnRotate,'State'),'on')
		set(handles.btnRotate,'State','off');
		rotate3d off
	end
		
	set([handles.slContours handles.btnResetLandmarks handles.btnPreview],'Enable','on');

	ud.storedViewpoint = get(handles.axMain,'View');
	ud.storedFrameStates = get([handles.btnShowGuides handles.btnShowPCs],'State');
	set(handles.axMain,'View',[0 90]);

	set([handles.btnShowGuides handles.btnShowMoreGuides handles.btnShowPCs],'State','off');
 	ud.hGuides = []; ud.hMoreGuides = []; ud.PCs = [];
	set(handles.figMain,'UserData',ud);
	
	updatePlots(handles,false);

	set(handles.axMain,'Visible','off');
	colorbar('SouthOutside');
%	axis(handles.axMain,'equal'); axis(handles.axMain,'tight');

	set(handles.figMain,'pointer','circle');
	set(handles.figMain,'WindowButtonDownFcn',@(hObject, eventdata) wbdLandmark(hObject, eventdata, handles));
	set(handles.figMain,'WindowButtonMotionFcn',@(hObject, eventdata) wbmLandmark(hObject, eventdata, handles));	% hoover over existing landmarks
	set(handles.axMain,'DrawMode','fast');

end

function btnContour_OffCallback(hObject, eventdata, handles)
% hObject    handle to btnContour (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

	ud = get(handles.figMain,'UserData');
	if isfield(ud,'storedViewpoint') && ~isempty(ud.storedViewpoint)
		set(handles.axMain,'View',ud.storedViewpoint);
		ud.storedViewpoint = [];
	end
	if isfield(ud,'disabledCtrls') && ~isempty(ud.disabledCtrls)
		set(ud.disabledCtrls,'Enable','on');
		ud.disabledCtrls = [];
	end
	set(handles.figMain,'UserData',ud);

	set([handles.slContours handles.btnResetLandmarks handles.btnPreview],'Enable','off');

	% restore the view from before
	updatePlots(handles,false); 
	
	if isfield(ud,'storedFrameStates') && ~isempty(ud.storedFrameStates)
		set(handles.btnShowGuides,'State',ud.storedFrameStates{1});
		set(handles.btnShowPCs,'State',ud.storedFrameStates{2});
	end

	set(handles.figMain,'WindowButtonMotionFcn',[]);
	set(handles.figMain,'WindowButtonDownFcn',@(hObject, eventdata) figMain_WindowButtonDownFcn(hObject, eventdata, handles));
	set(handles.figMain,'WindowButtonUpFcn',@(hObject, eventdata) figMain_WindowButtonUpFcn(hObject, eventdata, handles));
	set(handles.axMain,'DrawMode','normal');
	set(handles.figMain,'Pointer','arrow')
	
end

function wbdLandmark(hObject, eventdata, handles)

	cp = get(handles.axMain,'CurrentPoint');
	if ~axHittest(cp,handles.axMain), return, end

	ud = get(handles.figMain,'UserData');
	t = hooverTest(cp,handles,ud); 
	
    
	% left click with shift - tape measure
	if strcmp(get(hObject,'SelectionType'),'extend')
		
			xinit = cp(1,1); yinit = cp(1,2);
			hold(handles.axMain,'on');
			h = plot(handles.axMain,xinit,yinit,'Marker','x','MarkerSize',10,'MarkerFaceColor','b');
			hold(handles.axMain,'off');
		
 			set(handles.figMain,'WindowButtonMotionFcn',@(hObject, eventdata) wbmTrackTape(hObject, eventdata, handles));				
 			set(handles.figMain,'WindowButtonUpFcn',@(hObject, eventdata) wbuTrackTape(hObject, eventdata, handles));
	
	% double click on existing landmark - set contour line position
	elseif strcmp(get(hObject,'SelectionType'),'open') && t
        
		pos = points2real(ud.data,cp(1,1:2));
		slPos = round(get(handles.slContours,'Value'));
		
		zMax = max(ud.data(:,3));
		zMin = min(ud.data(:,3));
		lhs = pos(3):2:zMax;
		rhs = pos(3):-2:zMin;
		ud.contours = [fliplr(rhs(2:end)) lhs];
		set(handles.figMain,'UserData',ud);
		
		ud = updatePlots(handles,false,4);
		drawnow;

    % left click
	elseif strcmp(get(hObject,'SelectionType'),'normal')

		% first landmark - initialize 
		if ~isfield(ud,'landmarkPts') || isempty(ud.landmarkPts)
			data = get(ud.hMainPlot,'zdata');
			if iscell(data), data = data{1}; end % contour returns a cell 
			ud.zMax = max(data(:));
 			ud.landmarkPts = [];
 			ud.hLandmarks = [];
		end

		% move existing landmark?
		if ~isempty(ud.landmarkPts) && t
			
			if (isfield(ud,'hLabel') && ~isempty(ud.hLabel))
				delete(ud.hLabel);
				ud.hLabel = [];
			end
			
			ud.t = t;
			set(handles.figMain,'WindowButtonMotionFcn',@(hObject, eventdata) wbmTrackLandmark(hObject, eventdata, handles));				
			set(handles.figMain,'WindowButtonUpFcn',@(hObject, eventdata) wbuLandmark(hObject, eventdata, handles));
		
		% add new landmark
		else
			
			ud.landmarkPts = [ud.landmarkPts; cp(1,1:3)];

			hold(handles.axMain,'on');
			h = plot(handles.axMain,cp(1,1),cp(1,2),'Marker','.','MarkerSize',20,'MarkerFaceColor','b');
			hold(handles.axMain,'off');
			ud.hLandmarks = [ud.hLandmarks h];

		end
	
	% right click on existing landmark (delete landmark)
	elseif strcmp(get(hObject,'SelectionType'),'alt') && t

		delete(ud.hLandmarks(t));
		ud.landmarkPts(t,:) = [];
		ud.hLandmarks(t) = [];
		if (isfield(ud,'hLabel') && ~isempty(ud.hLabel))
			delete(ud.hLabel);
			ud.hLabel = [];
		end	

	end
	
	set(handles.figMain,'UserData',ud);
	
	function wbmTrackTape(hObject, eventdata, handles)

		cp = get(handles.axMain,'CurrentPoint');
		if ~axHittest(cp,handles.axMain), return, end

		xdat = [xinit cp(1,1)];
		ydat = [yinit cp(1,2)];
		set(h,'XData',xdat,'YData',ydat);
		drawnow;
		D = sqrt((xdat(1)-xdat(2)).^2 + (ydat(1)-ydat(2)).^2);
		set(handles.txtDistance,'String',sprintf('%0.2f',D));

	end

	function wbuTrackTape(hObject, eventdata, handles)
		
		delete(h);
		set(handles.txtDistance,'String','');
		
		set(hObject,'WindowButtonUpFcn',[]);
		set(handles.figMain,'WindowButtonDownFcn',@(hObject, eventdata) wbdLandmark(hObject, eventdata, handles));
		set(handles.figMain,'WindowButtonMotionFcn',@(hObject, eventdata) wbmLandmark(hObject, eventdata, handles));	% hoover over existing landmarks
 		
	end

	
	function wbuLandmark(hObject, eventdata, handles)
		
		cp = get(handles.axMain,'CurrentPoint');
		if ~axHittest(cp,handles.axMain), return, end		

		ud = get(handles.figMain,'UserData');

		% left click
		if strcmp(get(hObject,'SelectionType'),'normal')		
			ud.landmarkPts(ud.t,:) = cp(1,1:3);
			set(ud.hLandmarks(ud.t),'Xdata',cp(1,1),'Ydata',cp(1,2));
			ud.t = [];
			set(handles.figMain,'UserData',ud);
			drawnow;
			
		end
		
		set(hObject,'WindowButtonUpFcn',[]);
		set(hObject,'WindowButtonMotionFcn',@(hObject, eventdata) wbmLandmark(hObject, eventdata, handles));
		set(hObject,'WindowButtonDownFcn',@(hObject, eventdata) wbdLandmark(hObject, eventdata, handles));
 		
	end

	function wbmTrackLandmark(hObject, eventdata, handles)
		cp = get(handles.axMain,'CurrentPoint');
		
		ud = get(handles.figMain,'UserData');
		ud.landmarkPts(ud.t,:) = cp(1,1:3);
		set(ud.hLandmarks(ud.t),'Xdata',cp(1,1),'Ydata',cp(1,2));
		set(handles.figMain,'UserData',ud);
		
	end

	function wbdAddVertex(hObject, eventdata, handles, x, y, i)
		ud = get(handles.figMain,'UserData');
		if isempty(ud.hMarkerE), return; end
		ud.polyPts = [ud.polyPts(1:i,:); [x y]; ud.polyPts(i+1:end,:)];
 		ud.hMarker = [ud.hMarker(1:i) nan ud.hMarker(i+1:end)];
		ud.hl = [ud.hl(1:i) nan ud.hl(i+1:end)];
		polyPts = [ud.polyPts; ud.polyPts(1,:)];
		set(ud.hl(i),'XData',[polyPts(i,1) x],'YData',[polyPts(i,2) y],'ZData',[ud.zMax ud.zMax]);
 		ud.hl(i+1) = line('XData',[x polyPts(i+2,1)],'YData',[y polyPts(i+2,2)],'ZData',[ud.zMax ud.zMax],'Marker','.','MarkerSize',20,'color','b','LineWidth',2);
		set(handles.figMain,'UserData',ud);
	end

	function wbdDragPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		ud.wbm = get(hObject,'WindowButtonMotionFcn');
		set(hObject,'WindowButtonMotionFcn',@(hObject, eventdata) wbmDragPolygon(hObject, eventdata, handles));
		set(handles.figMain,'UserData',ud);
	end

	function wbuDragPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		set(hObject,'WindowButtonDownFcn','');
		set(hObject,'WindowButtonMotionFcn',ud.wbm);
	end

	function wbmDragPolygon(hObject, eventdata, handles)
		ud = get(handles.figMain,'UserData');
		cp = get(handles.axMain,'CurrentPoint');

		i1 = ud.currVert;
		i2 = ud.currVert-1;
		if i2==0, i2 = numel(ud.hl); end
			
		XData = get(ud.hl(i1),'XData');
		YData = get(ud.hl(i1),'YData');
		XData(1,1) = cp(1,1);
		YData(1,1) = cp(1,2);
		set(ud.hl(i1),'XData',XData,'YData',YData);
		ud.polyPts(i1,1:2) = cp(1,1:2);
		
		XData = get(ud.hl(i2),'XData');
		YData = get(ud.hl(i2),'YData');
		XData(1,2) = cp(1,1);
		YData(1,2) = cp(1,2);
		set(ud.hl(i2),'XData',XData,'YData',YData);
		ud.polyPts(i1,1:2) = cp(1,1:2);
		
		set(ud.hMarker(i1),'XData',cp(1,1),'YData',cp(1,2));

		set(handles.figMain,'UserData',ud);
	end

	function Iall = intersections(polyPts,cp)
		Iall = []; return
		
	 	% check if current line does not intersect with other lines
		% http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
		curLine = [polyPts(end,:); cp(1,1:2)];
		A = curLine(1,:); B = curLine(2,:);
		Iall = [];
		for i = 1:size(polyPts,1)-1
			tempLine = [polyPts(i,:); polyPts(i+1,:)];
			C = tempLine(1,:); D = tempLine(2,:);
			Iall = [Iall; intersectPts(A,B,C,D)];
		end
		
	end

end

function wbmLandmark(hObject, eventdata, handles)

		cp = get(handles.axMain,'CurrentPoint');
		if ~axHittest(cp,handles.axMain), return, end

		ud = get(handles.figMain,'UserData');
		
		% snap to the closest landmark point
		if isfield(ud,'landmarkPts') && ~isempty(ud.landmarkPts)
			t = hooverTest(cp,handles,ud);
		
			if t && (~isfield(ud,'hLabel') || isempty(ud.hLabel))
				ud.hLandmarks
				set(ud.hLandmarks(t),'Color','r');
				ud.hLabel = text(ud.landmarkPts(t,1),ud.landmarkPts(t,2),sprintf('L%d',t),'Color','r','FontWeight','bold','VerticalAlignment','top','HorizontalAlignment','right');
			elseif ~t && (isfield(ud,'hLabel') && ~isempty(ud.hLabel))
				set(ud.hLandmarks,'Color','b');
				delete(ud.hLabel);
				ud.hLabel = [];				
			end
		end
		
		set(handles.figMain,'UserData',ud);
		drawnow;
		
end

function out = hooverTest(cp,handles,ud)
	out = 0;
	if isfield(ud,'landmarkPts') && ~isempty(ud.landmarkPts)

		xTol = diff(get(handles.axMain,'XLim'))/100;
		yTol = diff(get(handles.axMain,'YLim'))/100;

		dist = sum((ones(size(ud.landmarkPts,1),1)*cp(1,1:2) - ud.landmarkPts(:,1:2)).^2,2);
		[dummy,minIdx] = min(dist);

		if (abs(ud.landmarkPts(minIdx,1)-cp(1,1))<xTol) && (abs(ud.landmarkPts(minIdx,2)-cp(1,2))<yTol)
			out = minIdx;
		end
	end
end
	
function slContours_Callback(hObject, eventdata, handles)
% hObject    handle to slContours (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
	ud = get(handles.figMain,'UserData');

	pos = round(get(handles.slContours,'Value'));
	set(handles.txtContours,'String',num2str(pos));
	set(handles.slContours,'Value',pos);
	
	ud.contours = pos;
    ud.gridRegenerated = 0;
	set(handles.figMain,'UserData',ud);

	updatePlots(handles,false,4);
    
end

function btnResetLandmarks_ClickedCallback(hObject, eventdata, handles)

	ud = get(handles.figMain,'UserData');	
	
	if isfield(ud,'hLandmarks') && ~isempty(ud.hLandmarks)
		delete(ud.hLandmarks);
		ud.landmarkPts = [];
		ud.hLandmarks = [];
	end
	
	set(handles.figMain,'UserData',ud);
end


function btnAxisFill_ClickedCallback(hObject, eventdata, handles)
	axis(handles.axMain,'fill');
end

function btnCopy_ClickedCallback(hObject, eventdata, handles)
	print(get(hObject,'UserData'), '-dmeta');
end

function btnExport_ClickedCallback(hObject, eventdata, handles)

	ud = get(handles.figMain,'UserData');
	data = get(hObject,'UserData');
	landmarkPts = data{1};
	areaData = data{2};
	filter = {'*.csv','CSV files'};

	% write XYZ file
	fname = [ud.fname(1:end-4) '_XYZ.csv'];
	[fname,pathname] = uiputfile(filter,'Export landmark XYZ file',[ud.pathname '\' fname]);
	
	if ~isequal(fname,0) && ~isequal(pathname,0)

		fid = fopen([pathname fname],'w');
		%fwrite(fid,sprintf('"POINT_ID","X","Y","RASTERVALU"\n'),'char');
		fwrite(fid,sprintf('"POINT_ID","X","Y","Z"\n'),'char');
        for i = 1:size(landmarkPts,1)
			fwrite(fid,sprintf('"L%d",%0.6f,%0.6f,%0.6f\n',i,landmarkPts(i,:)),'char');
		end
		fclose(fid);

		ud.pathname = pathname;
		ud.landmarkPathname = pathname;
	end
	
	% write P2P file
	fname = [ud.fname(1:end-4) '_P2P.csv'];
	[fname,pathname] = uiputfile(filter,'Export landmark P2P file',[ud.pathname '\' fname]);
	
	if ~isequal(fname,0) && ~isequal(pathname,0)

		t = landmarkPts;
		dist = sqrt(((t.*t)*ones(size(t,2),size(t,1)) - 2*(t*t') + ones(size(t,1),size(t,2))*(t'.*t')));

		fid = fopen([pathname fname],'w');
        fwrite(fid,'"UID",');
		for i = 1:size(landmarkPts,1)
			fwrite(fid,sprintf('"L%d"',i));
			if i<size(dist,1), fwrite(fid,sprintf(','),'char');
			else fwrite(fid,sprintf('\n'),'char');
			end
			
		end
		
		for i = 1:size(dist,1)
			fwrite(fid,sprintf('"L%d",',i),'char');
			for j = 1:size(dist,2)
				fwrite(fid,sprintf('%0.6f',dist(i,j)),'char');
				if j<size(dist,2), fwrite(fid,sprintf(','),'char');
				else fwrite(fid,sprintf('\n'),'char');
				end
			end
		end
		
		fclose(fid);

		ud.pathname = pathname;
		ud.landmarkPathname = pathname;
	end
	
	% write JPEG file
	filter = {'*.jp*g','JPEG files'};
	fname = [ud.fname(1:end-4) '.jpeg'];
	[fname,pathname] = uiputfile(filter,'Export landmark JPEG file',[ud.pathname '\' fname]);
	
	if ~isequal(fname,0) && ~isequal(pathname,0)

		hFig = figure('Visible','off');

		if numel(ud.contours) == 1, v = linspace(min(ud.data(:,3)),max(ud.data(:,3)),ud.contours+2);
		else v = ud.contours;
		end
		contourf(ud.X,ud.Y,ud.Z,v);
		
		%contourf(ud.X,ud.Y,ud.Z,linspace(min(ud.data(:,3)),max(ud.data(:,3)),ud.contours));
		hAx = get(hFig,'CurrentAxes');

		hold(hAx,'on');
		names = cell(1,size(ud.landmarkPts,1));
		for i = 1:size(ud.landmarkPts,1)
			plot(hAx,ud.landmarkPts(i,1),ud.landmarkPts(i,2),'.','MarkerSize',20,'MarkerFaceColor','b');
			names{i} = sprintf('L%d',i);
			text(ud.landmarkPts(i,1),ud.landmarkPts(i,2),names{i},'Color','r','FontWeight','bold','VerticalAlignment','top','HorizontalAlignment','right');
		end
		hold(hAx,'off');
		
		daspect(hAx,daspect(handles.axMain));
		set(hAx,'Visible','off');
		updateColormap(handles);		

		set(hAx,'Position',[0 0 1 1]);
		saveas(hFig,[pathname fname]);
		close(hFig);
		ud.pathname = pathname;
		ud.landmarkPathname = pathname;
	end

	% write AREA file
	fname = [ud.fname(1:end-4) '_AREA.csv'];
	[fname,pathname] = uiputfile(filter,'Export contour AREA file',[ud.pathname '\' fname]);
	
	if ~isequal(fname,0) && ~isequal(pathname,0)

		fid = fopen([pathname fname],'w');
		fwrite(fid,sprintf('"AREA","CENTROID-X","CENTROID-Y","Z"\n'),'char');
		for i = 1:size(areaData,1)
			fwrite(fid,sprintf('%0.6f,%0.6f,%0.6f,%0.6f\n',areaData(i,:)),'char');
		end
		fclose(fid);

		ud.pathname = pathname;
		ud.landmarkPathname = pathname;
	end

	
end

function btnPreview_ClickedCallback(hObject, eventdata, handles)
	
	ud = get(handles.figMain,'UserData');
	if isfield(ud,'landmarkPts') && ~isempty(ud.landmarkPts)
		
		ud.landmarkPts = points2real(ud.data,ud.landmarkPts);
		
		hFig = figure('NumberTitle','off','Name','Landmark preview','MenuBar','none');
%  		pos = get(hFig,'position');
% 		set(hFig,'position',[pos(1)-(pos(3)*1.5-pos(1))*.5 pos(2)-(pos(4)*1.5-pos(2))*.25 pos(3)*1.5 pos(4)*1.5]);
		if ~isfield(ud,'hFigToClose'), ud.hFigToClose = []; end
		ud.hFigToClose = [ud.hFigToClose hFig];
		hBar = uitoolbar(hFig);
	
		if numel(ud.contours) == 1, v = linspace(min(ud.data(:,3)),max(ud.data(:,3)),ud.contours+2);
		else v = ud.contours;
		end
		[C,h] = contourf(ud.X,ud.Y,ud.Z,v);
        [Area,Centroid,IN,Z] = Contour2Area1(C);
		areaData = [Area',Centroid',Z'];

		btnExport = uipushtool(hBar,'TooltipString','Export landmarks','CData',get(handles.btnSave,'CData'));
		set(btnExport,'ClickedCallback',@(hObject, eventdata) btnExport_ClickedCallback(hObject,eventdata,handles),'UserData',{ud.landmarkPts,areaData});

		btnCopy = uipushtool(hBar,'TooltipString','Copy figure to clipboard','Separator','on','CData',get(handles.btnAxisFill,'CData'),'UserData',hFig);
		set(btnCopy,'ClickedCallback',@(hObject, eventdata) btnCopy_ClickedCallback(hObject,eventdata,handles));

		hAx = get(hFig,'CurrentAxes');

		hold(hAx,'on');
		names = cell(1,size(ud.landmarkPts,1));
		for i = 1:size(ud.landmarkPts,1)
			plot(hAx,ud.landmarkPts(i,1),ud.landmarkPts(i,2),'.','MarkerSize',20,'MarkerFaceColor','b');
			names{i} = sprintf('L%d',i);
			text(ud.landmarkPts(i,1),ud.landmarkPts(i,2),names{i},'Color','r','FontWeight','bold','VerticalAlignment','top','HorizontalAlignment','right');
		end
		hold(hAx,'off');
		
		daspect(hAx,daspect(handles.axMain));
		set(hAx,'Visible','off');
		updateColormap(handles);

		
		set(hAx,'Position',[0.0 0.05 0.3 0.90]);
		colorbar('SouthOutside');

		t = ud.landmarkPts;
		dist = sqrt(((t.*t)*ones(size(t,2),size(t,1)) - 2*(t*t') + ones(size(t,1),size(t,2))*(t'.*t')));

% 		v = caxis;
% 		hc = get(h,'Children');
% 		CData = get(hc,'FaceVertexCData');
% 		cIdx = round(([CData{:}]-v(1))*63/(v(2)-v(1)));
% 		cm = colormap;
		
% 		% dendrogram
% 		[I,J] = find(IN);
% 		JI = sortrows([J,I],[1 2]);
% 		uJ = unique(J);
% 		uJI = zeros(numel(uJ),2);
% 		for i = 1:numel(uJ)
% 			maxParent = max(JI(JI(:,1) == uJ(i),2));
% 			uJI(i,:) = [uJ(i) maxParent];
% 		end
% 		hTree = axes('Units','normalized','Position',[0.3 0.06 0.3 0.28]);
% 		p = [0 uJI(:,2)'];
% 		[x,y] = treelayout(p);
% 		f = find(p~=0);
% 		pp = p(f);
% 		X = [x(f); x(pp); NaN(size(f))];
% 		Y = [y(f); y(pp); NaN(size(f))];
% 		X = X(:); Y = Y(:);
% % 		nanIdx = find(~isnan(cIdx));
% % 		c = nan(numel(cIdx),3);
% % 		c(nanIdx,:) = cm(1+cIdx(nanIdx),:);
% 		plot(hTree,x,y,'ro',X, Y, 'r-');
% % 		hold(hTree,'on');
% % 		for i = 1:numel(nanIdx)
% % 			plot (x(nanIdx(i)), y(nanIdx(i)), '.','MarkerSize',20,'Color',c(nanIdx(i),:));
% % 		end
% % 		hold(hTree,'off');
% 		
% % 		treeplot(treeVec,repmat('r',1,numel(treeVec)));%,cm(1+cIdx(~isnan(cIdx)),:));
% 		axis tight;
% 		axis off;
% 
% 		count = size(p,2);
% 		x = x';	y = y';
% 		name1 = cellstr(num2str((1:count)'));
% 		text(x(:,1), y(:,1), name1, 'VerticalAlignment','bottom','HorizontalAlignment','right','FontSize',8);

		hTabXYZ = uitable(hFig,'ColumnName',{'X','Y','Z'},'RowName',names,'Units','normalized','Position',[0.61 0.52 0.38 0.43],'Data',ud.landmarkPts,'ColumnWidth','auto');
		hTabP2P = uitable(hFig,'ColumnName',names,'RowName',names,'Units','normalized',        'Position',[0.61 0.05 0.38 0.45],'Data',dist,'ColumnWidth','auto');
		hTabContour = uitable(hFig, ...
			'ColumnName',{'Area','Centroid X','Centroid Y','Z'}, ...
			'Units','normalized', ...
			'Position',[0.3 0.05 0.3 0.9], ...
			'Data',areaData, ...
			'ColumnWidth','auto', ...
			'ColumnFormat',{'long', 'long', 'long'});
		set(handles.figMain,'UserData',ud);
	end

end


function btnContourCrop_OnCallback(hObject, eventdata, handles)
	ud = get(handles.figMain,'UserData');
	
	ud.disabledCtrls = [handles.btnAutoRotate handles.btnRegenGrid handles.btnFlipUpDown ...
		handles.btnFlipLeftRight handles.btnFlipBackFront handles.btnRotateClockwise ...
		handles.btnRotateAnticlockwise handles.btnShowGuides handles.btnShowMoreGuides ...
		handles.btnShowPCs handles.ddPlotType handles.slYaw handles.slPitch handles.slRoll ...
		handles.txtYaw handles.txtPitch handles.txtRoll handles.btnResetView handles.btnSelectTool ...
		handles.btnRotate handles.btnZeroNan handles.btnSelectPolygonTool handles.btnContour handles.btnExportView];
	set(ud.disabledCtrls,'Enable','off');
	
	if strcmpi(get(handles.btnRotate,'State'),'on')
		set(handles.btnRotate,'State','off');
		rotate3d off
	end	
		
	set([handles.slContours handles.slContourCrop handles.btnStoreChanges handles.btnResetChanges handles.txtContourCrop],'Enable','on');
%    slContourCrop_Callback(handles.slContourCrop,eventdata,handles);
    
	ud.storedViewpoint = get(handles.axMain,'View');
	ud.storedFrameStates = get([handles.btnShowGuides handles.btnShowPCs],'State');
	set(handles.axMain,'View',[0 90]);

	set([handles.btnShowGuides handles.btnShowMoreGuides handles.btnShowPCs],'State','off');
% 	btnShowGuides_Callback(handles.btnShowGuides,eventdata,handles);
% 	btnShowPCs_Callback(handles.btnShowPCs,eventdata,handles);
 	ud.hGuides = []; ud.PCs = [];

	set(handles.figMain,'UserData',ud);
	
	%updatePlots(handles,false);
    slContourCrop_Callback(handles.slContourCrop, eventdata, handles);
    
	set(handles.axMain,'Visible','off');
	colorbar('SouthOutside');
end

function btnContourCrop_OffCallback(hObject, eventdata, handles)

	ud = get(handles.figMain,'UserData');
	if isfield(ud,'storedViewpoint') && ~isempty(ud.storedViewpoint)
		set(handles.axMain,'View',ud.storedViewpoint);
		ud.storedViewpoint = [];
	end
	if isfield(ud,'disabledCtrls') && ~isempty(ud.disabledCtrls)
		set(ud.disabledCtrls,'Enable','on');
		ud.disabledCtrls = [];
    end
    ud.data = ud.orgData;
    %ud.X = [];
	set(handles.figMain,'UserData',ud);

	set([handles.slContours handles.slContourCrop handles.btnStoreChanges handles.btnResetChanges handles.txtContourCrop],'Enable','off');

	% restore the view from before
	updatePlots(handles,false); 
	
	if isfield(ud,'storedFrameStates') && ~isempty(ud.storedFrameStates)
		set(handles.btnShowGuides,'State',ud.storedFrameStates{1});
		set(handles.btnShowPCs,'State',ud.storedFrameStates{2});
	end

end

function slContourCrop_Callback(hObject, eventdata, handles)
% hObject    handle to slContourCrop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

 	ud = get(handles.figMain,'UserData');

    pos = get(handles.slContourCrop,'Value');
    set(handles.txtContourCrop,'String',sprintf('%0.3f',pos));
    
	mask = (ud.orgData(:,3)<=pos);
	ud.data = ud.orgData;
	ud.data(~mask,3) = nan;
%  	ud.data = ud.orgData(ud.orgData(:,3)<=pos,:);

	% ud.F = TriScatteredInterp(ud.data(:,1),ud.data(:,2),ud.data(:,3));
 	%ud.X = [];

   	set(handles.figMain,'UserData',ud);
   	updatePlots(handles);

end

function slContourCrop_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slContourCrop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end
end

function txtContourCrop_Callback(hObject, eventdata, handles)

    posStr = get(hObject,'String');
    try
        pos = round(1000*str2double(posStr))/1000;
    catch
        pos = get(handle.slContourCrop,'Max');
    end

    if pos>get(handles.slContourCrop,'Max') 
        pos = get(handles.slContourCrop,'Max');
    elseif pos<get(handles.slContourCrop,'Min')
        pos = get(handles.slContourCrop,'Min');
    end
    
    set(handles.slContourCrop,'Value',pos);
    set(hObject,'String',sprintf('%0.3f',pos));
    
    drawnow;
    slContourCrop_Callback(handles.slContourCrop, eventdata, handles);
end

function txtContourCrop_CreateFcn(hObject, eventdata, handles)
% hObject    handle to txtContourCrop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

end

function btnOldGrid_ClickedCallback(hObject, eventdata, handles)
	updatePlots(handles);
end

function btnNormXY_OnCallback(hObject, eventdata, handles)
 	ud = get(handles.figMain,'UserData');
	ud.data(:,1:2) = zscore(ud.data(:,1:2));
	set(handles.figMain,'UserData',ud);
	updatePlots(handles);
end

function btnNormZ_OnCallback(hObject, eventdata, handles)
 	ud = get(handles.figMain,'UserData');
	ud.data(:,3) = zscore(ud.data(:,3));
	set(handles.figMain,'UserData',ud);
	updatePlots(handles);
end

function btnInterpError_ClickedCallback(hObject, eventdata, handles)

	h = waitbar(0,'Calculating the interpolation error. Please wait...','Visible','off','WindowStyle','modal');
	centerFigure(h); set(h,'Visible','on');

	ud = get(handles.figMain,'UserData');
	
	% calculate the interpolation error
	mask = isnan(ud.data(:,3));
	A = ud.data(~mask,1:2);
	
	mask = isnan(ud.Z(:));
	B = [ud.X(:) ud.Y(:)];
	B = B(~mask,:);
	
	M = zeros(1,size(B,1));
	for i = 1:size(B,1)
		D = sqrt(sum((ones(size(A,1),1)*B(i,:) - A).^2,2));
		D = sort(D);
		M(i) = mean(D(1:4));
		waitbar(i/size(B,1));
	end
	
	M = mean(M);
	close(h);
	
	msgbox(sprintf('Interpolation error: %0.4f',M));

end

function btnExportView_ClickedCallback(hObject, eventdata, handles)

	ud = get(handles.figMain,'UserData');

	filter = {'*.jp*g','JPEG files'};
	fname = [ud.fname(1:end-4) '.jpeg'];
	[fname,pathname] = uiputfile(filter,'Export landmark JPEG file',[ud.pathname '\' fname]);
	
	if ~isequal(fname,0) && ~isequal(pathname,0)

		hFig = figure('Visible','off');%,'Units','normalized','Position',[0,0,1,1]);
		axis;
		set(gca,'Position',[0 0 1 1]);
		updatePlots(handles,false,[],gca);
		saveas(hFig,[pathname fname]);
		close(hFig);
	
		ud.pathname = pathname;
		ud.landmarkPathname = pathname;
	end

end
