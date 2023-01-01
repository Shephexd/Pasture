#/bin/bash
python manage.py collectstatic --no-input
python manage.py migrate

sed -i 's,NGINX_SET_REAL_IP_FROM,'"$NGINX_SET_REAL_IP_FROM"',g' /etc/nginx/nginx.conf
sed -i 's,PROXY_PASS,'"$PROXY_PASS"',g' /etc/nginx/conf.d/webapp.conf
sed -i 's,RESOURCE_DIR,'"$RESOURCE_DIR"',g' /etc/nginx/conf.d/webapp.conf

nginx
gunicorn pasture.configs.wsgi:application --bind unix://$PROXY_PASS