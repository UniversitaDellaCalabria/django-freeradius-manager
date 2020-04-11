# Django Freeradius Manager
---------------------------

A Freeradius 3 Manager with Accounts provisioning.

This project was started upon a fork of django-freeradius.

![Landing page](gallery/1.png)


#### Features

- Full localization support based on Django
-
-

#### Setup

Install django things
````
apt install python3 python3-dev libmariadb-client python3-pip
virtualenv -ppython3 env
source env/bin/activate
pip3 install -r requirements.txt
````

Create a Database for this project, put these credentials in `freerad_manager/settingslocal.py`
````
mysql -u root -e "CREATE DATABASE IF NOT EXISTS radius; GRANT ALL ON radius.* TO radius@'%' IDENTIFIED BY '$RADIUS_PWD'; \
flush privileges;"
````

An example of `freerad_manager/settingslocal.py` configuration here
````
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'radius',
        'HOST': '10.0.3.85',
        'USER': 'radius',
        'PASSWORD': 'radiussecret',
        'PORT': '',
    }
}

RADIUS_SERVER = '10.0.3.85'
RADIUS_PORT = 1812
RADIUS_SECRET = 'radiussecret'
````

Freeradius setup
````
apt install freeradius freeradius-mysql mariadb-server
````

Configure Freeradius
````
export RADCONFD="/etc/freeradius/3.0/"
export RADIUS_PWD="radiussecret"

systemctl freeradius stop

pushd $RADCONFD

# this is useless because django-freeradius-manager creates automatically the database
# otherwise create a db with these schemas
# find . -type f | grep schema.sql  | grep mysql | grep main | grep -v extras
# mysql -u radius --password=$RADIUS_PWD radius < $RADCONFD./mods-config/sql/main/mysql/schema.sql

# configure mysql db connection
sed -i 's/.*driver = "rlm_sql_null"/driver = "rlm_sql_mysql"/' $RADCONFD/mods-available/sql
sed -i 's/dialect = "sqlite"/dialect = "mysql"/' $RADCONFD/mods-available/sql
sed -i 's/#.*server = "localhost"/       server = "localhost"/' $RADCONFD/mods-available/sql
sed -i 's/#.*port = 3306/       port = 3306/' $RADCONFD/mods-available/sql
sed -i 's/#.*login = "radius"/        login = "radius"/' $RADCONFD/mods-available/sql
sed -i 's/#.*password = "radpass"/        password = "'$RADIUS_PWD'"/' $RADCONFD/mods-available/sql

# sqlcounter patch
sed -i 's|dialect = ${modules.sql.dialect}|dialect = mysql|g' $RADCONFD/mods-available/sqlcounter

# enable mysql module
ln -s $RADCONFD/mods-available/sql        $RADCONFD/mods-enabled/
ln -s $RADCONFD/mods-available/sqlcounter $RADCONFD/mods-enabled/

# auth
# inner-tunnel
sed -i 's|session {|session {\nsql|' $RADCONFD/sites-enabled/inner-tunnel
# default
sed -i 's|session {|session {\nsql|' $RADCONFD/sites-enabled/default
sed -i 's|accounting {|accounting {\nsql|' $RADCONFD/sites-enabled/default

# disable unused eap methods
sed -i 's|default_eap_type = md5|default_eap_type = peap|' $RADCONFD/mods-available/eap

# also rememebr to disable md5 auth in eap module ...

# logging
# it could be done also with this:
# radiusconfig -setconfig auth yes
# radiusconfig -setconfig auth_badpass yes
# sed -i 's|logdir = ${localstatedir}/log/radius|logdir = /var/log/radius|' $RADCONFD/radiusd.conf
# sed -i 's|auth_badpass = no|auth_badpass = yes|g' $RADCONFD/radiusd.conf
# sed -i 's|auth_goodpass = no|auth_goodpass = yes|g' $RADCONFD/radiusd.conf
sed -i 's|auth = no|auth = yes|g' $RADCONFD/radiusd.conf

# better use those in RDBMS ...
# accounting logs, readable in $logdir/acct/*
# sed -i 's|#.*auth_log|auth_log|' $RADCONFD/sites-enabled/default
# sed -i 's|#\s*reply_log$|reply_log|' $RADCONFD/sites-enabled/default
# radlast command workaround (.f option doesn't still work)
# mkdir -p /usr/local/var/log/radius/
# ln -s /var/log/freeradius/radwtmp /usr/local/var/log/radius/
````

See `README_freeradius.md` for a fine tuning od SQL queries.


#### Credits

- OpenWISP community
- CNR IMAA guys


#### Author

- Giuseppe De Marco
