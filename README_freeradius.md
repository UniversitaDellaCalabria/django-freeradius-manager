Freeradius customization
------------------------

Permit only expirable Rad Checks
--------------------------------

Django-Freeradius provides the possibility to extend the freeradius query in order to introduce is_active and valid_until checks.

An example using MySQL is:

````
# /etc/freeradius/mods-config/sql/main/mysql/queries.conf
authorize_check_query = "SELECT id, username, attribute, value, op \
                         FROM ${authcheck_table} \
                         WHERE username = '%{SQL-User-Name}' \
                         AND is_active = TRUE \
                         AND valid_until >= CURDATE() \
                         ORDER BY id"
````


Post-Auth
---------

in `/etc/freeradius/3.0/mods-config/sql/main/mysql/queries.conf` configure this way

````
# post-auth {
        # Write SQL queries to a logfile. This is potentially useful for bulk inserts
        # when used with the rlm_sql_null driver.
#       logfile = ${logdir}/post-auth.sql

        # query = "\
                # INSERT INTO ${..postauth_table} \
                        # (username, pass, reply, authdate) \
                # VALUES ( \
                        # '%{SQL-User-Name}', \
                        # '%{%{User-Password}:-%{Chap-Password}}', \
                        # '%{reply:Packet-Type}', \
                        # '%S')"
# }


post-auth {
        # Write SQL queries to a logfile. This is potentially useful for bulk inserts
        # when used with the rlm_sql_null driver.
#       logfile = ${logdir}/post-auth.sql

        query = "\
                INSERT INTO ${..postauth_table} \
                        (username, \
                         reply, \
                         authdate, \
                         callingstationid, \
                         calledstationid \
                         ) \
                VALUES ( \
                        '%{SQL-User-Name}', \
                        '%{reply:Packet-Type}', \
                        '%S', \
                        '%{Calling-Station-Id}', \
                        '%{Called-Station-Id}' \
                        )"
}


In /etc/freeradius/3.0/mods-config/sql/main/mysql/queries.conf
````
post-auth {
        # Write SQL queries to a logfile. This is potentially useful for bulk inserts
        # when used with the rlm_sql_null driver.
#       logfile = ${logdir}/post-auth.sql

#       query = "\
#               INSERT INTO ${..postauth_table} \
#                       (username, pass, reply, authdate) \
#               VALUES(\
#                       '%{User-Name}', \
#                       '%{%{User-Password}:-Chap-Password}', \
#                       '%{reply:Packet-Type}', \
#                       NOW())"

        query = "\
                INSERT INTO ${..postauth_table} \
                        (authdate, username, outerid, innerid, cui, reply, calledstationid, callingstationid, eduroam_sp_country, operator_name, nas_identifier) \
                VALUES( \
                        NOW(), \
                        '%{User-Name}', \
                        '%{outer.request:User-Name}', \
                        '%{User-Name}', \
                        '%{%{reply:Chargeable-User-Identity}:-None}', \
                        '%{reply:Packet-Type}', \
                        '%{Called-Station-Id}', \
                        '%{Calling-Station-Id}', \
                        '%{eduroam-SP-Country}', \
                        '%{Operator-Name}', \
                        '%{NAS-Identifier}'\
                        )"

}
````
