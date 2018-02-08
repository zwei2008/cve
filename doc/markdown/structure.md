# CVE-Search structure
## Mongo Database Structure
This section describes the structure of the Mongo database. There are
 two types of collections, data and management.
The data collections, which are listed below, are the collections that
 are filled by the sources CVE-Search uses.
By default, these are the official sources.

**These are the data collections:**

| Collection | Source     | Description |
| :---       | :---       | :---        |
| cves       | NVD NIST   | All the official vulnerabilities, released by NIST. Items in this collection have all info related to each CVE |
| cpe        | NVD NIST   | All the official products, released by NIST. Some of these have a human readable title. |
| cpeother   | CVE-Search | CVE-Search has a script to fill this database, using the original CPE's and generating titles for them. |
| cwe        | NVD NIST   | Information about Common Weaknesses, as published by NIST |
| d2sec      | d2sec.com  | Information about CVE's, as released by d2sec |
| info       | CVE-Search | Information about the Mongo Database updates. |

**These are the management collections:**

| Collection     | Description |
| :---           | :---        |
| ranking        | Self-set ranking for specific CPE's that are more important to specific groups |
| mgmt_blacklist | List of CPE's that have to be excluded from the web view. More about this [here](./webcomponent.md) |
| mgmt_whitelist | List of CPE's that have to be marked in the web view. More about this [here](./webcomponent.md)> |
| mgmt_users     | List of users who have access to the administrative panel. More about this [here](./webcomponent.md) |

By default, the Mongo database name is cvedb. This connection for the
 database is made on localhost, port 27017.

##Redis Cache Database
The Redis Caching server is used to speed up the searches in the web
 component. It is also used for the notifications script.<br />
By default, The database used for speeding up the searches is database
 number 10, and the vendor database is database 11.<br />
The vendor database (database 10) contains four collections. These are:

 * prefix
 * types
 * vendors
 * Products

These lists get filled by the *db_cpe_browser.py* script, and create
 "links" to each other. Feel free to take a look at *db_cpe_browser.py*
 to learn how it works. <br /> <br />
The notifications cache has a structure where it keeps track of:

 * Organisations
 * CPEs
 * MailTo destination

Feel free to take a look at *db_notifications.py* to learn how it works.
