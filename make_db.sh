export USER='freerad'
export PASS='thatpass'
export HOST='%'
export DB='freerad'

mysql -u root -e "\
CREATE DATABASE ${DB} CHARACTER SET utf8 COLLATE utf8_general_ci;\
GRANT ALL PRIVILEGES ON ${DB}.* TO ${USER}@'${HOST}' IDENTIFIED BY '${PASS}';;"
