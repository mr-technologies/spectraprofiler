$ARGYLL_VERSION="3.2.0"

$ErrorActionPreference="Stop"
pushd "${PSScriptRoot}"
$failed=$true
try
{
	mkdir tmp

	"Installing Python modules..."
	python -m pip install --upgrade pip
	pip install --upgrade colormath Pillow

	"Downloading Argyll CMS and dcamprof..."
	Invoke-WebRequest -Uri "https://www.argyllcms.com/Argyll_V${ARGYLL_VERSION}_win64_exe.zip" -OutFile "tmp\Argyll_V${ARGYLL_VERSION}_win64_exe.zip"
	Invoke-WebRequest -Uri https://torger.se/anders/files/dcamprof-1.0.6-win64.zip -OutFile tmp\dcamprof-1.0.6-win64.zip
	"Unpacking..."
	Expand-Archive -Path "tmp\Argyll_V${ARGYLL_VERSION}_win64_exe.zip" -DestinationPath tmp
	Expand-Archive -Path tmp\dcamprof-1.0.6-win64.zip -DestinationPath tmp

	"Copying necessary files..."
	cp "tmp\Argyll_V${ARGYLL_VERSION}\ref\ColorChecker.cht" ..\res\layout.cht
	cp "tmp\Argyll_V${ARGYLL_VERSION}\bin\scanin.exe" ..\res
	cp tmp\dcamprof-1.0.6-win64\dcamprof.exe ..\res
	cp tmp\dcamprof-1.0.6-win64\data-examples\cc24_ref-new.cie ..\res\reference.cie
	cp tmp\dcamprof-1.0.6-win64\data-examples\cc24-layout.json ..\res\layout.json

	"Application dependencies (except for OpenCV) has been successfully installed."
	"You can now remove ${PWD}\tmp."
	$failed=$false
}
catch
{
	$_
}
finally
{
	popd
	if($failed)
	{
		Read-Host "Failed! Remove ${PWD}\tmp before trying again. Press Enter to exit"
	}
	else
	{
		Read-Host "Success! Press Enter to exit"
	}
}
