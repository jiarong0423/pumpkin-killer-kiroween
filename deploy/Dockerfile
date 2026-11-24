FROM nginx:alpine

RUN sed '1,/^types {/d;/^}/d' /etc/nginx/mime.types > /etc/nginx/pk_mime_body.types
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY sw.js /usr/share/nginx/html/sw.js
COPY manifest.webmanifest /usr/share/nginx/html/manifest.webmanifest
COPY icons/icon-192.png /usr/share/nginx/html/icons/icon-192.png
COPY icons/icon-512.png /usr/share/nginx/html/icons/icon-512.png
COPY icons/icon-maskable-512.png /usr/share/nginx/html/icons/icon-maskable-512.png
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY assets/ /usr/share/nginx/html/assets/
COPY shared/ /usr/share/nginx/html/shared/

EXPOSE 80
