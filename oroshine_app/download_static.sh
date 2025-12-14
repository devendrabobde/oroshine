#!/bin/bash

# Define the target static directory
TARGET_DIR="/home/nikhil/project/oroshine/oroshine_app/oroshine_webapp/static"

echo "-----------------------------------------------------"
echo "Starting Static File Download for OroShine Dental App"
echo "Target Directory: $TARGET_DIR"
echo "-----------------------------------------------------"

# 1. Create Directory Structure
echo "Creating directory structure..."
mkdir -p "$TARGET_DIR/css"
mkdir -p "$TARGET_DIR/js"
mkdir -p "$TARGET_DIR/lib/animate"
mkdir -p "$TARGET_DIR/lib/owlcarousel/assets"
mkdir -p "$TARGET_DIR/lib/tempusdominus/css"
mkdir -p "$TARGET_DIR/lib/tempusdominus/js"
mkdir -p "$TARGET_DIR/lib/twentytwenty"
mkdir -p "$TARGET_DIR/lib/wow"
mkdir -p "$TARGET_DIR/lib/easing"
mkdir -p "$TARGET_DIR/lib/waypoints"
mkdir -p "$TARGET_DIR/lib/jquery"
mkdir -p "$TARGET_DIR/lib/fontawesome/css"
mkdir -p "$TARGET_DIR/lib/fontawesome/webfonts"
mkdir -p "$TARGET_DIR/lib/bootstrap-icons"
mkdir -p "$TARGET_DIR/lib/bootstrap-icons/fonts"


# 2. Download Core Bootstrap 5 & Custom JS
echo "Downloading Bootstrap 5..."
curl -L -o "$TARGET_DIR/css/bootstrap.min.css" "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
curl -L -o "$TARGET_DIR/js/bootstrap.bundle.min.js" "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"

# Create a placeholder main.js if it doesn't exist
if [ ! -f "$TARGET_DIR/js/main.js" ]; then
    echo "Creating default main.js..."
    touch "$TARGET_DIR/js/main.js"
fi

# Create a placeholder style.css if it doesn't exist
if [ ! -f "$TARGET_DIR/css/style.css" ]; then
    echo "Creating default style.css..."
    touch "$TARGET_DIR/css/style.css"
fi

# 3. Download jQuery (CRITICAL: Loaded first)
echo "Downloading jQuery..."
curl -L -o "$TARGET_DIR/lib/jquery/jquery.min.js" "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.4/jquery.min.js"

# 4. Download Icon Libraries
echo "Downloading FontAwesome (CSS & Webfonts)..."
curl -L -o "$TARGET_DIR/lib/fontawesome/css/all.min.css" "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
# Download essential webfonts referenced by all.min.css
curl -L -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-solid-900.woff2" "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.woff2"
curl -L -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-brands-400.woff2" "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-brands-400.woff2"
curl -L -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-regular-400.woff2" "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-regular-400.woff2"

echo "Downloading Bootstrap Icons..."
curl -L -o "$TARGET_DIR/lib/bootstrap-icons/bootstrap-icons.css" "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
curl -L -o "$TARGET_DIR/lib/bootstrap-icons/fonts/bootstrap-icons.woff2" "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/fonts/bootstrap-icons.woff2"

# 5. Download Animation & Scroll Plugins
echo "Downloading WOW.js & Animate.css..."
curl -L -o "$TARGET_DIR/lib/wow/wow.min.js" "https://cdnjs.cloudflare.com/ajax/libs/wow/1.1.2/wow.min.js"
curl -L -o "$TARGET_DIR/lib/animate/animate.min.css" "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"

echo "Downloading Easing & Waypoints..."
curl -L -o "$TARGET_DIR/lib/easing/jquery.easing.min.js" "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js"
curl -L -o "$TARGET_DIR/lib/waypoints/waypoints.min.js" "https://cdnjs.cloudflare.com/ajax/libs/waypoints/4.0.1/jquery.waypoints.min.js"

# 6. Download Owl Carousel
echo "Downloading Owl Carousel..."
curl -L -o "$TARGET_DIR/lib/owlcarousel/owl.carousel.min.js" "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/owl.carousel.min.js"
curl -L -o "$TARGET_DIR/lib/owlcarousel/assets/owl.carousel.min.css" "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css"
curl -L -o "$TARGET_DIR/lib/owlcarousel/assets/owl.theme.default.min.css" "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.theme.default.min.css"

# 7. Download Tempus Dominus (Datepicker)
echo "Downloading Tempus Dominus..."
# Note: Using version 6 to match the file naming convention, though HTML might need syntax updates for v6
curl -L -o "$TARGET_DIR/lib/tempusdominus/js/tempus-dominus.min.js" "https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.7.16/dist/js/tempus-dominus.min.js"
curl -L -o "$TARGET_DIR/lib/tempusdominus/css/tempus-dominus.min.css" "https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.7.16/dist/css/tempus-dominus.min.css"

# 8. Download TwentyTwenty (Image Comparison)
echo "Downloading TwentyTwenty..."
# These specific files are often not on standard CDNs as cleanly, downloading from raw git source or similar reliable cdn
curl -L -o "$TARGET_DIR/lib/twentytwenty/jquery.twentytwenty.js" "https://raw.githubusercontent.com/zurb/twentytwenty/master/js/jquery.twentytwenty.js"
curl -L -o "$TARGET_DIR/lib/twentytwenty/jquery.event.move.js" "https://raw.githubusercontent.com/stephband/jquery.event.move/master/js/jquery.event.move.js"
curl -L -o "$TARGET_DIR/lib/twentytwenty/twentytwenty.css" "https://raw.githubusercontent.com/zurb/twentytwenty/master/css/twentytwenty.css"

echo "-----------------------------------------------------"
echo "Download Complete!"
echo "Files have been saved to $TARGET_DIR"
echo "Please run 'python manage.py collectstatic' if you are in production mode."
echo "-----------------------------------------------------"