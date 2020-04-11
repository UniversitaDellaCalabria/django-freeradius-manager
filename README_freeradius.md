Setup freeradius
----------------

A quanto già disposto qui: https://github.com/peppelinux/UniTools/blob/master/freeradius/freeradius_3.0.12_debian9.setup.sh

aggiungere i seguenti:

Post-Auth
---------

in /etc/freeradius/3.0/mods-config/sql/main/mysql/queries.conf, estendere
post-auth così

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

# TODO extends schema to handle the following attributes
# Operator-Name, eduroam-SP-Country, Chargeable-User-Identity, NAS-Identifier
# vedi: https://www.eventi.garr.it/it/ws18/home/materiali-conferenza-2017/presentazioni-3/310-ws2018-slide-albrizio/file

````

Modificare il model così:

````
            outerid text,
            innerid text NOT NULL,
            ChargeableUserIdentity text,
            reply text,
            callingstationid text,
            calledstationid text,
            eduroamSPCountry text,
            OperatorName text,
            NASIdentifier text
````


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
