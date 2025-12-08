@echo off
setlocal

:: --- Configuration ---
:: Relative path from this script to the static folder
set "STATIC_DIR=oroshine_webapp\static"

echo ===================================================
echo  Downloading Static Files for OroShine (Windows)
echo  Target: %STATIC_DIR%
echo ===================================================

:: --- Create Directory Structure ---
echo [1/3] Creating directory structure...

if not exist "%STATIC_DIR%" mkdir "%STATIC_DIR%"

:: FontAwesome Folders
if not exist "%STATIC_DIR%\lib\fontawesome\css" mkdir "%STATIC_DIR%\lib\fontawesome\css"
if not exist "%STATIC_DIR%\lib\fontawesome\webfonts" mkdir "%STATIC_DIR%\lib\fontawesome\webfonts"

:: Bootstrap Icons Folders
if not exist "%STATIC_DIR%\lib\bootstrap-icons\fonts" mkdir "%STATIC_DIR%\lib\bootstrap-icons\fonts"

:: Other Library Folders
if not exist "%STATIC_DIR%\lib\owlcarousel\assets" mkdir "%STATIC_DIR%\lib\owlcarousel\assets"
if not exist "%STATIC_DIR%\lib\animate" mkdir "%STATIC_DIR%\lib\animate"
if not exist "%STATIC_DIR%\lib\tempusdominus\css" mkdir "%STATIC_DIR%\lib\tempusdominus\css"
if not exist "%STATIC_DIR%\lib\tempusdominus\js" mkdir "%STATIC_DIR%\lib\tempusdominus\js"
if not exist "%STATIC_DIR%\lib\twentytwenty" mkdir "%STATIC_DIR%\lib\twentytwenty"
if not exist "%STATIC_DIR%\lib\jquery" mkdir "%STATIC_DIR%\lib\jquery"
if not exist "%STATIC_DIR%\lib\wow" mkdir "%STATIC_DIR%\lib\wow"
if not exist "%STATIC_DIR%\lib\easing" mkdir "%STATIC_DIR%\lib\easing"
if not exist "%STATIC_DIR%\lib\waypoints" mkdir "%STATIC_DIR%\lib\waypoints"
if not exist "%STATIC_DIR%\css" mkdir "%STATIC_DIR%\css"
if not exist "%STATIC_DIR%\js" mkdir "%STATIC_DIR%\js"
if not exist "%STATIC_DIR%\img" mkdir "%STATIC_DIR%\img"

:: --- Download Files ---
echo [2/3] Downloading assets...

:: 1. FontAwesome (CSS + Webfonts)
echo    - FontAwesome...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" -o "%STATIC_DIR%\lib\fontawesome\css\all.min.css"
:: Webfonts
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-solid-900.woff2"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-solid-900.woff"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.ttf" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-solid-900.ttf"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff2" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-regular-400.woff2"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-regular-400.woff"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.ttf" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-regular-400.ttf"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff2" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-brands-400.woff2"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-brands-400.woff"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.ttf" -o "%STATIC_DIR%\lib\fontawesome\webfonts\fa-brands-400.ttf"

:: 2. Bootstrap Icons (CSS + Fonts)
echo    - Bootstrap Icons...
curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" -o "%STATIC_DIR%\lib\bootstrap-icons\bootstrap-icons.css"
:: Fonts
curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff2" -o "%STATIC_DIR%\lib\bootstrap-icons\fonts\bootstrap-icons.woff2"
curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff" -o "%STATIC_DIR%\lib\bootstrap-icons\fonts\bootstrap-icons.woff"

:: 3. Owl Carousel
echo    - Owl Carousel...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css" -o "%STATIC_DIR%\lib\owlcarousel\assets\owl.carousel.min.css"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/owl.carousel.min.js" -o "%STATIC_DIR%\lib\owlcarousel\owl.carousel.min.js"

:: 4. Animate.css
echo    - Animate.css...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" -o "%STATIC_DIR%\lib\animate\animate.min.css"

:: 5. Tempus Dominus & Moment.js
echo    - Tempus Dominus (Fixed)...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js" -o "%STATIC_DIR%\lib\tempusdominus\js\moment.min.js"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/moment-timezone/0.5.43/moment-timezone.min.js" -o "%STATIC_DIR%\lib\tempusdominus\js\moment-timezone.min.js"
:: Corrected URLs: Removed the extra hyphen in 'tempus-dominus'
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/tempusdominus-bootstrap-4/5.39.0/css/tempusdominus-bootstrap-4.min.css" -o "%STATIC_DIR%\lib\tempusdominus\css\tempusdominus-bootstrap-4.min.css"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/tempusdominus-bootstrap-4/5.39.0/js/tempusdominus-bootstrap-4.min.js" -o "%STATIC_DIR%\lib\tempusdominus\js\tempusdominus-bootstrap-4.min.js"

:: 6. jQuery
echo    - jQuery...
curl -L -f "https://code.jquery.com/jquery-3.6.0.min.js" -o "%STATIC_DIR%\lib\jquery\jquery.min.js"

:: 7. WOW.js
echo    - WOW.js...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/wow/1.1.2/wow.min.js" -o "%STATIC_DIR%\lib\wow\wow.min.js"

:: 8. jQuery Easing
echo    - jQuery Easing...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js" -o "%STATIC_DIR%\lib\easing\jquery.easing.min.js"

:: 9. Waypoints
echo    - Waypoints...
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/waypoints/4.0.1/jquery.waypoints.min.js" -o "%STATIC_DIR%\lib\waypoints\jquery.waypoints.min.js"

:: 10. Bootstrap 5 (Main)
echo    - Bootstrap 5 & Maps...
curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" -o "%STATIC_DIR%\css\bootstrap.min.css"
:: Download Map file to fix 404 warning
curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css.map" -o "%STATIC_DIR%\css\bootstrap.min.css.map"

curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" -o "%STATIC_DIR%\js\bootstrap.bundle.min.js"
:: Download Map file to fix 404 warning
curl -L -f "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js.map" -o "%STATIC_DIR%\js\bootstrap.bundle.min.js.map"

:: 11. Twentytwenty (Fixed)
:: 11. Twentytwenty (Fixed - using stable move.js)
echo    - Twentytwenty...
:: 1. Download the OFFICIAL stable jquery.event.move (v2.0.0) to fix the "indexOf" error
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/jquery.event.move/2.0.0/jquery.event.move.min.js" -o "%STATIC_DIR%\lib\twentytwenty\jquery.event.move.js"

:: 2. Download the Twentytwenty slider plugin itself
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/mhayes-twentytwenty/1.0.0/js/jquery.twentytwenty.js" -o "%STATIC_DIR%\lib\twentytwenty\jquery.twentytwenty.js"
curl -L -f "https://cdnjs.cloudflare.com/ajax/libs/mhayes-twentytwenty/1.0.0/css/twentytwenty.css" -o "%STATIC_DIR%\lib\twentytwenty\twentytwenty.css"
echo.
echo [3/3] Done! Please verify that files exist in %STATIC_DIR%
pause