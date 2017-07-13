alter table django_site add column folder_name varchar(255);
alter table django_site add column subdomains varchar(255);

INSERT INTO `django_site` (`id`, `domain`, `name`, `folder_name`, `subdomains`)
VALUES
       (2, 'localhost', 'localhost', 'localhost', ''),
       (3, 'test.localhost', 'Test Journal', 'test', '');
