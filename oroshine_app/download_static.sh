# #!/bin/bash
# set -e

# # ==============================================================================
# # 1. PERMANENT PATH FIX (Works in CI/CD, Docker, Local, AWS)
# # ==============================================================================

# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# TARGET_DIR="$SCRIPT_DIR/oroshine_webapp/static"

# echo "-----------------------------------------------------"
# echo "🚀 Starting Static Asset Pipeline"
# echo "📍 Environment: $(uname -s)"
# echo "📂 Script Root: $SCRIPT_DIR"
# echo "🎯 Target Dir:  $TARGET_DIR"
# echo "-----------------------------------------------------"

# # ==============================================================================
# # 2. CLEANUP
# # ==============================================================================
# rm -rf "$TARGET_DIR/lib"
# rm -rf "$TARGET_DIR/webfonts"

# # ==============================================================================
# # 3. DIRECTORY STRUCTURE (✅ FIXED)
# # ==============================================================================
# mkdir -p "$TARGET_DIR/css" "$TARGET_DIR/js" "$TARGET_DIR/webfonts"

# mkdir -p "$TARGET_DIR/lib/animate"
# mkdir -p "$TARGET_DIR/lib/owlcarousel/assets"
# mkdir -p "$TARGET_DIR/lib/tempusdominus/css"
# mkdir -p "$TARGET_DIR/lib/tempusdominus/js"
# mkdir -p "$TARGET_DIR/lib/twentytwenty"
# mkdir -p "$TARGET_DIR/lib/wow"
# mkdir -p "$TARGET_DIR/lib/waypoints"
# mkdir -p "$TARGET_DIR/lib/jquery"
# mkdir -p "$TARGET_DIR/lib/easing"              
# mkdir -p "$TARGET_DIR/lib/fontawesome/css"
# mkdir -p "$TARGET_DIR/lib/fontawesome/webfonts"
# mkdir -p "$TARGET_DIR/lib/bootstrap-icons/fonts"

# # ==============================================================================
# # 4. DOWNLOAD PIPELINE
# # ==============================================================================

# echo "⬇️  [1/6] Core Frameworks..."
# curl -s -L -o "$TARGET_DIR/css/bootstrap.min.css" \
#   "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"

# curl -s -L -o "$TARGET_DIR/js/bootstrap.bundle.min.js" \
#   "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"

# curl -s -L -o "$TARGET_DIR/lib/jquery/jquery.min.js" \
#   "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"

# echo "⬇️  [2/6] FontAwesome..."
# curl -s -L -o "$TARGET_DIR/lib/fontawesome/css/all.min.css" \
#   "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"

# curl -s -L -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-solid-900.woff2" \
#   "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2"

# curl -s -L -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-brands-400.woff2" \
#   "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff2"

# curl -s -L -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-regular-400.woff2" \
#   "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff2"

# cp "$TARGET_DIR/lib/fontawesome/webfonts/"* "$TARGET_DIR/webfonts/"

# echo "⬇️  [3/6] Bootstrap Icons..."
# curl -s -L -o "$TARGET_DIR/lib/bootstrap-icons/bootstrap-icons.css" \
#   "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css"

# curl -s -L -o "$TARGET_DIR/lib/bootstrap-icons/fonts/bootstrap-icons.woff2" \
#   "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2"

# echo "⬇️  [4/6] Dental Features..."
# curl -s -L -o "$TARGET_DIR/lib/twentytwenty/jquery.twentytwenty.js" \
#   "https://raw.githubusercontent.com/zurb/twentytwenty/master/js/jquery.twentytwenty.js"

# curl -s -L -o "$TARGET_DIR/lib/twentytwenty/jquery.event.move.js" \
#   "https://raw.githubusercontent.com/stephband/jquery.event.move/master/js/jquery.event.move.js"

# curl -s -L -o "$TARGET_DIR/lib/twentytwenty/twentytwenty.css" \
#   "https://raw.githubusercontent.com/zurb/twentytwenty/master/css/twentytwenty.css"

# echo "⬇️  [5/6] UI Plugins..."
# curl -s -L -o "$TARGET_DIR/lib/owlcarousel/owl.carousel.min.js" \
#   "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/owl.carousel.min.js"

# curl -s -L -o "$TARGET_DIR/lib/owlcarousel/assets/owl.carousel.min.css" \
#   "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css"

# curl -s -L -o "$TARGET_DIR/lib/owlcarousel/assets/owl.theme.default.min.css" \
#   "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.theme.default.min.css"

# curl -s -L -o "$TARGET_DIR/lib/tempusdominus/js/tempus-dominus.min.js" \
#   "https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.9.4/dist/js/tempus-dominus.min.js"

# curl -s -L -o "$TARGET_DIR/lib/tempusdominus/css/tempus-dominus.min.css" \
#   "https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.9.4/dist/css/tempus-dominus.min.css"

# echo "⬇️  [6/6] Animations..."
# curl -s -L -o "$TARGET_DIR/lib/wow/wow.min.js" \
#   "https://cdnjs.cloudflare.com/ajax/libs/wow/1.1.2/wow.min.js"

# curl -s -L -o "$TARGET_DIR/lib/animate/animate.min.css" \
#   "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"

# curl -s -L -o "$TARGET_DIR/lib/waypoints/waypoints.min.js" \
#   "https://cdnjs.cloudflare.com/ajax/libs/waypoints/4.0.1/jquery.waypoints.min.js"

# curl -s -L -o "$TARGET_DIR/lib/easing/jquery.easing.min.js" \
#   "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js"

# # ==============================================================================
# # 5. SAFE DEFAULT FILES
# # ==============================================================================
# [ -f "$TARGET_DIR/js/main.js" ] || touch "$TARGET_DIR/js/main.js"
# [ -f "$TARGET_DIR/css/style.css" ] || touch "$TARGET_DIR/css/style.css"

# echo "✅ SUCCESS: All static assets ready"






























#!/bin/bash
set -e

# ==============================================================================
# 1. PATH SETUP
# ==============================================================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TARGET_DIR="$SCRIPT_DIR/oroshine_webapp/static"

echo "-----------------------------------------------------"
echo "🚀 Bootstrap 5 Static Asset Pipeline"
echo "📂 Script Root: $SCRIPT_DIR"
echo "🎯 Target Dir:  $TARGET_DIR"
echo "-----------------------------------------------------"

# ==============================================================================
# 2. CLEANUP (REMOVE LEGACY LIBS)
# ==============================================================================
rm -rf "$TARGET_DIR/lib"
rm -rf "$TARGET_DIR/webfonts"

# ==============================================================================
# 3. DIRECTORY STRUCTURE (BOOTSTRAP 5)
# ==============================================================================
mkdir -p "$TARGET_DIR/css" "$TARGET_DIR/js" "$TARGET_DIR/webfonts"

mkdir -p "$TARGET_DIR/lib/jquery"
mkdir -p "$TARGET_DIR/lib/owlcarousel/assets"
mkdir -p "$TARGET_DIR/lib/animate"
mkdir -p "$TARGET_DIR/lib/datepicker"
mkdir -p "$TARGET_DIR/lib/fontawesome/css"
mkdir -p "$TARGET_DIR/lib/fontawesome/webfonts"
mkdir -p "$TARGET_DIR/lib/bootstrap-icons/font/fonts"
mkdir -p "$TARGET_DIR/lib/twentytwenty"

# ==============================================================================
# 4. DOWNLOAD PIPELINE
# ==============================================================================

echo "⬇️  [1/6] Bootstrap 5..."
curl -fsSL -o "$TARGET_DIR/css/bootstrap.min.css" \
https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css

curl -fsSL -o "$TARGET_DIR/js/bootstrap.bundle.min.js" \
https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js

echo "⬇️  [2/6] jQuery (Owl Carousel only)..."
curl -fsSL -o "$TARGET_DIR/lib/jquery/jquery.min.js" \
https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js

echo "⬇️  [3/6] Font Awesome..."
curl -fsSL -o "$TARGET_DIR/lib/fontawesome/css/all.min.css" \
https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css

curl -fsSL -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-solid-900.woff2" \
https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2

curl -fsSL -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-brands-400.woff2" \
https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff2

curl -fsSL -o "$TARGET_DIR/lib/fontawesome/webfonts/fa-regular-400.woff2" \
https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff2

cp "$TARGET_DIR/lib/fontawesome/webfonts/"* "$TARGET_DIR/webfonts/"

echo "⬇️  [4/6] Bootstrap Icons..."
curl -fsSL -o "$TARGET_DIR/lib/bootstrap-icons/bootstrap-icons.css" \
https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css

curl -fsSL -o "$TARGET_DIR/lib/bootstrap-icons/font/fonts/bootstrap-icons.woff2" \
https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2

echo "⬇️  [5/6] UI Components..."
curl -fsSL -o "$TARGET_DIR/lib/owlcarousel/owl.carousel.min.js" \
https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/owl.carousel.min.js

curl -fsSL -o "$TARGET_DIR/lib/owlcarousel/assets/owl.carousel.min.css" \
https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css

curl -fsSL -o "$TARGET_DIR/lib/owlcarousel/assets/owl.theme.default.min.css" \
https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.theme.default.min.css

echo "⬇️  [6/6] Datepicker + Animations..."
curl -fsSL -o "$TARGET_DIR/lib/datepicker/datepicker.min.js" \
https://cdn.jsdelivr.net/npm/vanillajs-datepicker@1.3.4/dist/js/datepicker.min.js

curl -fsSL -o "$TARGET_DIR/lib/datepicker/datepicker.min.css" \
https://cdn.jsdelivr.net/npm/vanillajs-datepicker@1.3.4/dist/css/datepicker.min.css

curl -fsSL -o "$TARGET_DIR/lib/animate/animate.min.css" \
https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css

echo "⬇️  [Optional] TwentyTwenty..."
curl -fsSL -o "$TARGET_DIR/lib/twentytwenty/jquery.twentytwenty.js" \
https://raw.githubusercontent.com/zurb/twentytwenty/master/js/jquery.twentytwenty.js

curl -fsSL -o "$TARGET_DIR/lib/twentytwenty/jquery.event.move.js" \
https://raw.githubusercontent.com/stephband/jquery.event.move/master/js/jquery.event.move.js

curl -fsSL -o "$TARGET_DIR/lib/twentytwenty/twentytwenty.css" \
https://raw.githubusercontent.com/zurb/twentytwenty/master/css/twentytwenty.css

# ==============================================================================
# 5. SAFE DEFAULT FILES
# ==============================================================================
[ -f "$TARGET_DIR/js/main.js" ] || touch "$TARGET_DIR/js/main.js"
[ -f "$TARGET_DIR/css/style.css" ] || touch "$TARGET_DIR/css/style.css"

echo "✅ SUCCESS: Bootstrap 5 static assets ready"
