#!/bin/bash
set -e

# Configuration
STATIC_DIR="oroshine_webapp/static"

echo "==================================================="
echo " Downloading Static Files for OroShine (Linux)"
echo " Target: $STATIC_DIR"
echo "==================================================="

echo "[1/3] Creating directory structure..."

# Create all necessary directories
mkdir -p "$STATIC_DIR/lib/fontawesome/css"
mkdir -p "$STATIC_DIR/lib/fontawesome/webfonts"
mkdir -p "$STATIC_DIR/lib/bootstrap-icons/fonts"
mkdir -p "$STATIC_DIR/lib/bootstrap-icons"
mkdir -p "$STATIC_DIR/lib/owlcarousel/assets"
mkdir -p "$STATIC_DIR/lib/animate"
mkdir -p "$STATIC_DIR/lib/tempusdominus/css"
mkdir -p "$STATIC_DIR/lib/tempusdominus/js"
mkdir -p "$STATIC_DIR/lib/twentytwenty"
mkdir -p "$STATIC_DIR/lib/jquery"
mkdir -p "$STATIC_DIR/lib/wow"
mkdir -p "$STATIC_DIR/lib/easing"
mkdir -p "$STATIC_DIR/lib/waypoints"
mkdir -p "$STATIC_DIR/css"
mkdir -p "$STATIC_DIR/js"
mkdir -p "$STATIC_DIR/img"

download() {
    url="$1"
    dest="$2"
    echo "   -> Downloading $(basename "$dest")..."
    # -L follows redirects, --fail exits on 404
    curl -L --fail "$url" -o "$dest"
}

echo "[2/3] Downloading assets..."

# 1. FontAwesome (CSS + Fonts)
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" "$STATIC_DIR/lib/fontawesome/css/all.min.css"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2" "$STATIC_DIR/lib/fontawesome/webfonts/fa-solid-900.woff2"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff" "$STATIC_DIR/lib/fontawesome/webfonts/fa-solid-900.woff"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.ttf" "$STATIC_DIR/lib/fontawesome/webfonts/fa-solid-900.ttf"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff2" "$STATIC_DIR/lib/fontawesome/webfonts/fa-regular-400.woff2"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff" "$STATIC_DIR/lib/fontawesome/webfonts/fa-regular-400.woff"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.ttf" "$STATIC_DIR/lib/fontawesome/webfonts/fa-regular-400.ttf"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff2" "$STATIC_DIR/lib/fontawesome/webfonts/fa-brands-400.woff2"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff" "$STATIC_DIR/lib/fontawesome/webfonts/fa-brands-400.woff"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.ttf" "$STATIC_DIR/lib/fontawesome/webfonts/fa-brands-400.ttf"

# 2. Bootstrap Icons (CSS + Fonts)
download "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" "$STATIC_DIR/lib/bootstrap-icons/bootstrap-icons.css"
download "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff2" "$STATIC_DIR/lib/bootstrap-icons/fonts/bootstrap-icons.woff2"
download "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff" "$STATIC_DIR/lib/bootstrap-icons/fonts/bootstrap-icons.woff"

# 3. Owl Carousel
download "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css" "$STATIC_DIR/lib/owlcarousel/assets/owl.carousel.min.css"
download "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/owl.carousel.min.js" "$STATIC_DIR/lib/owlcarousel/owl.carousel.min.js"

# 4. Animate.css
download "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" "$STATIC_DIR/lib/animate/animate.min.css"

# 5. Tempus Dominus
download "https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js" "$STATIC_DIR/lib/tempusdominus/js/moment.min.js"
download "https://cdnjs.cloudflare.com/ajax/libs/moment-timezone/0.5.43/moment-timezone.min.js" "$STATIC_DIR/lib/tempusdominus/js/moment-timezone.min.js"
download "https://cdnjs.cloudflare.com/ajax/libs/tempus-dominus-bootstrap-4/5.39.0/css/tempusdominus-bootstrap-4.min.css" "$STATIC_DIR/lib/tempusdominus/css/tempusdominus-bootstrap-4.min.css"
download "https://cdnjs.cloudflare.com/ajax/libs/tempus-dominus-bootstrap-4/5.39.0/js/tempusdominus-bootstrap-4.min.js" "$STATIC_DIR/lib/tempusdominus/js/tempusdominus-bootstrap-4.min.js"

# 6. jQuery
download "https://code.jquery.com/jquery-3.6.0.min.js" "$STATIC_DIR/lib/jquery/jquery.min.js"

# 7. WOW.js
download "https://cdnjs.cloudflare.com/ajax/libs/wow/1.1.2/wow.min.js" "$STATIC_DIR/lib/wow/wow.min.js"

# 8. jQuery Easing
download "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js" "$STATIC_DIR/lib/easing/jquery.easing.min.js"

# 9. Waypoints
download "https://cdnjs.cloudflare.com/ajax/libs/waypoints/4.0.1/jquery.waypoints.min.js" "$STATIC_DIR/lib/waypoints/jquery.waypoints.min.js"

# 10. Bootstrap 5
download "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" "$STATIC_DIR/css/bootstrap.min.css"
download "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" "$STATIC_DIR/js/bootstrap.bundle.min.js"

# 11. Twentytwenty
download "https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/js/jquery.event.move.js" "$STATIC_DIR/lib/twentytwenty/jquery.event.move.js"
download "https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/js/jquery.twentytwenty.js" "$STATIC_DIR/lib/twentytwenty/jquery.twentytwenty.js"
download "https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/css/twentytwenty.css" "$STATIC_DIR/lib/twentytwenty/twentytwenty.css"

echo "[3/3] All files downloaded successfully!"