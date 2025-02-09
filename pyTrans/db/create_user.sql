CREATE USER 'writer'@'%' IDENTIFIED BY '02fc937cfc2cdf0bc23743ad846491d75bb34614';
GRANT SELECT (id_user, uuid) on ftrans.user TO 'writer'@'%';
GRANT SELECT (id_file, sha1) on ftrans.file TO 'writer'@'%';
GRANT SELECT on ftrans.landmark TO 'writer'@'%';
GRANT INSERT on ftrans.* TO 'writer'@'%';