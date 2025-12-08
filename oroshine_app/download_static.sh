#!/bin/bash
set -e

# Detect if we're in the static directory or project root
if [ -d "oroshine_webapp/static" ]; then
    STATIC_DIR="oroshine_webapp/static"
elif [ -d "static" ]; then
    STATIC_DIR="static"
else
    echo "❌ Error: Cannot find static directory"
    echo "Please run this script from either:"
    echo "  - Project root (where manage.py is)"
    echo "  - oroshine_webapp directory"
    exit 1
fi

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

download() {
    url="$1"
    dest="$2"
    echo "   -> Downloading $(basename "$dest")..."
    
    # Try download with retries
    max_attempts=3
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -L --fail --silent --show-error --connect-timeout 10 --max-time 30 "$url" -o "$dest" 2>/dev/null; then
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            echo "      ⚠️  Attempt $attempt failed, retrying..."
            attempt=$((attempt + 1))
            sleep 2
        else
            echo "      ❌ Failed after $max_attempts attempts"
            return 1
        fi
    done
}

echo "[2/3] Downloading assets..."

echo "📦 FontAwesome 6.5.1..."
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" "$STATIC_DIR/lib/fontawesome/css/all.min.css"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2" "$STATIC_DIR/lib/fontawesome/webfonts/fa-solid-900.woff2"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff2" "$STATIC_DIR/lib/fontawesome/webfonts/fa-regular-400.woff2"
download "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff2" "$STATIC_DIR/lib/fontawesome/webfonts/fa-brands-400.woff2"

echo "📦 Bootstrap Icons 1.11.3..."
download "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" "$STATIC_DIR/lib/bootstrap-icons/bootstrap-icons.css"
download "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2" "$STATIC_DIR/lib/bootstrap-icons/fonts/bootstrap-icons.woff2"
download "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff" "$STATIC_DIR/lib/bootstrap-icons/fonts/bootstrap-icons.woff"

echo "📦 Bootstrap 5.3.2..."
download "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" "$STATIC_DIR/css/bootstrap.min.css"
download "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css.map" "$STATIC_DIR/css/bootstrap.min.css.map"
download "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js" "$STATIC_DIR/js/bootstrap.bundle.min.js"
download "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js.map" "$STATIC_DIR/js/bootstrap.bundle.min.js.map"

echo "📦 Owl Carousel 2.3.4..."
download "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css" "$STATIC_DIR/lib/owlcarousel/assets/owl.carousel.min.css"
download "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.theme.default.min.css" "$STATIC_DIR/lib/owlcarousel/assets/owl.theme.default.min.css"
download "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/owl.carousel.min.js" "$STATIC_DIR/lib/owlcarousel/owl.carousel.min.js"

echo "📦 Animate.css 4.1.1..."
download "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" "$STATIC_DIR/lib/animate/animate.min.css"

echo "📦 Tempus Dominus v6 (Bootstrap 5)..."
download "https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.9.4/dist/css/tempus-dominus.min.css" "$STATIC_DIR/lib/tempusdominus/css/tempus-dominus.min.css"
download "https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.9.4/dist/js/tempus-dominus.min.js" "$STATIC_DIR/lib/tempusdominus/js/tempus-dominus.min.js"
download "https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" "$STATIC_DIR/lib/tempusdominus/js/popper.min.js"

echo "📦 jQuery 3.7.1..."
download "https://code.jquery.com/jquery-3.7.1.min.js" "$STATIC_DIR/lib/jquery/jquery.min.js"

echo "📦 WOW.js 1.1.2..."
download "https://cdnjs.cloudflare.com/ajax/libs/wow/1.1.2/wow.min.js" "$STATIC_DIR/lib/wow/wow.min.js"

echo "📦 jQuery Easing 1.4.1..."
download "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js" "$STATIC_DIR/lib/easing/easing.min.js"

echo "📦 Waypoints 4.0.1..."
download "https://cdnjs.cloudflare.com/ajax/libs/waypoints/4.0.1/jquery.waypoints.min.js" "$STATIC_DIR/lib/waypoints/waypoints.min.js"

echo "📦 Twentytwenty 1.0.0 (from GitHub)..."
# Try CDN first, fallback to GitHub
if ! download "https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/css/twentytwenty.css" "$STATIC_DIR/lib/twentytwenty/twentytwenty.css"; then
    echo "   -> Trying GitHub source..."
    download "https://raw.githubusercontent.com/zurb/twentytwenty/master/css/twentytwenty.css" "$STATIC_DIR/lib/twentytwenty/twentytwenty.css"
fi

if ! download "https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/js/jquery.event.move.js" "$STATIC_DIR/lib/twentytwenty/jquery.event.move.js"; then
    echo "   -> Trying GitHub source..."
    download "https://raw.githubusercontent.com/zurb/twentytwenty/master/js/jquery.event.move.js" "$STATIC_DIR/lib/twentytwenty/jquery.event.move.js"
fi

if ! download "https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/js/jquery.twentytwenty.js" "$STATIC_DIR/lib/twentytwenty/jquery.twentytwenty.js"; then
    echo "   -> Trying GitHub source..."
    download "https://raw.githubusercontent.com/zurb/twentytwenty/master/js/jquery.twentytwenty.js" "$STATIC_DIR/lib/twentytwenty/jquery.twentytwenty.js"
fi

echo ""
echo "==================================================="
echo "[3/3] ✅ Download complete!"
echo "==================================================="
echo ""
echo "📊 Verifying downloads..."

# Count downloaded files
total_files=$(find "$STATIC_DIR/lib" -type f 2>/dev/null | wc -l)
echo "   Total files: $total_files"

# List directory structure
echo ""
echo "📁 Directory structure:"
ls -lh "$STATIC_DIR/lib/" 2>/dev/null | grep "^d" | awk '{print "   " $9}'

echo ""
echo "✓ Bootstrap 5.3.2 (CSS + JS + Source Maps)"
echo "✓ FontAwesome 6.5.1 (woff2 fonts)"
echo "✓ Bootstrap Icons 1.11.3"
echo "✓ Tempus Dominus v6 (Bootstrap 5 compatible)"
echo "✓ jQuery 3.7.1"
echo "✓ Owl Carousel, Animate.css, WOW.js, Easing, Waypoints, Twentytwenty"
echo ""
echo "🔧 Next steps:"
echo "   1. python manage.py collectstatic --noinput"
echo "   2. Update templates to use new file paths"
echo ""
echo "📝 Important: Update JS file paths in templates:"
echo "   - lib/easing/easing.min.js (was jquery.easing.min.js)"
echo "   - lib/waypoints/waypoints.min.js (was jquery.waypoints.min.js)"
echo ""
echo "🚀 Ready for deployment!"