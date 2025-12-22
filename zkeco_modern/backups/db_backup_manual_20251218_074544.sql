-- MySQL dump 10.11
--
-- Host: 127.0.0.1    Database: 
-- ------------------------------------------------------
-- Server version	5.0.45-community-nt

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `mysql`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `mysql` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `mysql`;

--
-- Table structure for table `columns_priv`
--

DROP TABLE IF EXISTS `columns_priv`;
CREATE TABLE `columns_priv` (
  `Host` char(60) collate utf8_bin NOT NULL default '',
  `Db` char(64) collate utf8_bin NOT NULL default '',
  `User` char(16) collate utf8_bin NOT NULL default '',
  `Table_name` char(64) collate utf8_bin NOT NULL default '',
  `Column_name` char(64) collate utf8_bin NOT NULL default '',
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `Column_priv` set('Select','Insert','Update','References') character set utf8 NOT NULL default '',
  PRIMARY KEY  (`Host`,`Db`,`User`,`Table_name`,`Column_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Column privileges';

--
-- Dumping data for table `columns_priv`
--

LOCK TABLES `columns_priv` WRITE;
/*!40000 ALTER TABLE `columns_priv` DISABLE KEYS */;
/*!40000 ALTER TABLE `columns_priv` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `db`
--

DROP TABLE IF EXISTS `db`;
CREATE TABLE `db` (
  `Host` char(60) collate utf8_bin NOT NULL default '',
  `Db` char(64) collate utf8_bin NOT NULL default '',
  `User` char(16) collate utf8_bin NOT NULL default '',
  `Select_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Insert_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Update_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Delete_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Drop_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Grant_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `References_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Index_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Alter_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_tmp_table_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Lock_tables_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_view_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Show_view_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_routine_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Alter_routine_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Execute_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  PRIMARY KEY  (`Host`,`Db`,`User`),
  KEY `User` (`User`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Database privileges';

--
-- Dumping data for table `db`
--

LOCK TABLES `db` WRITE;
/*!40000 ALTER TABLE `db` DISABLE KEYS */;
/*!40000 ALTER TABLE `db` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `func`
--

DROP TABLE IF EXISTS `func`;
CREATE TABLE `func` (
  `name` char(64) collate utf8_bin NOT NULL default '',
  `ret` tinyint(1) NOT NULL default '0',
  `dl` char(128) collate utf8_bin NOT NULL default '',
  `type` enum('function','aggregate') character set utf8 NOT NULL,
  PRIMARY KEY  (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='User defined functions';

--
-- Dumping data for table `func`
--

LOCK TABLES `func` WRITE;
/*!40000 ALTER TABLE `func` DISABLE KEYS */;
/*!40000 ALTER TABLE `func` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `help_category`
--

DROP TABLE IF EXISTS `help_category`;
CREATE TABLE `help_category` (
  `help_category_id` smallint(5) unsigned NOT NULL,
  `name` char(64) NOT NULL,
  `parent_category_id` smallint(5) unsigned default NULL,
  `url` char(128) NOT NULL,
  PRIMARY KEY  (`help_category_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='help categories';

--
-- Dumping data for table `help_category`
--

LOCK TABLES `help_category` WRITE;
/*!40000 ALTER TABLE `help_category` DISABLE KEYS */;
INSERT INTO `help_category` VALUES (1,'Geographic',0,''),(2,'Polygon properties',30,''),(3,'WKT',30,''),(4,'Numeric Functions',34,''),(5,'MBR',30,''),(6,'Control flow functions',34,''),(7,'Transactions',31,''),(8,'Account Management',31,''),(9,'Point properties',30,''),(10,'Encryption Functions',34,''),(11,'LineString properties',30,''),(12,'Logical operators',34,''),(13,'Miscellaneous Functions',34,''),(14,'Functions and Modifiers for Use with GROUP BY',31,''),(15,'Information Functions',34,''),(16,'Storage Engines',31,''),(17,'Comparison operators',34,''),(18,'Bit Functions',34,''),(19,'Table Maintenance',31,''),(20,'Data Types',31,''),(21,'Triggers',31,''),(22,'Geometry constructors',30,''),(23,'GeometryCollection properties',1,''),(24,'Administration',31,''),(25,'Data Manipulation',31,''),(26,'Geometry relations',30,''),(27,'Language Structure',31,''),(28,'Date and Time Functions',34,''),(29,'WKB',30,''),(30,'Geographic Features',31,''),(31,'Contents',0,''),(32,'Geometry properties',30,''),(33,'String Functions',34,''),(34,'Functions',31,''),(35,'Stored Routines',31,''),(36,'Data Definition',31,'');
/*!40000 ALTER TABLE `help_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `help_keyword`
--

DROP TABLE IF EXISTS `help_keyword`;
CREATE TABLE `help_keyword` (
  `help_keyword_id` int(10) unsigned NOT NULL,
  `name` char(64) NOT NULL,
  PRIMARY KEY  (`help_keyword_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='help keywords';

--
-- Dumping data for table `help_keyword`
--

LOCK TABLES `help_keyword` WRITE;
/*!40000 ALTER TABLE `help_keyword` DISABLE KEYS */;
INSERT INTO `help_keyword` VALUES (0,'JOIN'),(1,'REPEAT'),(2,'SERIALIZABLE'),(3,'REPLACE'),(4,'RETURNS'),(5,'MASTER_SSL_CA'),(6,'NCHAR'),(7,'COLUMNS'),(8,'WORK'),(9,'DATETIME'),(10,'MODE'),(11,'OPEN'),(12,'INTEGER'),(13,'ESCAPE'),(14,'VALUE'),(15,'GEOMETRYCOLLECTIONFROMWKB'),(16,'SQL_BIG_RESULT'),(17,'DROP'),(18,'EVENTS'),(19,'MONTH'),(20,'INFO'),(21,'DUPLICATE'),(22,'REPLICATION'),(23,'INNODB'),(24,'YEAR_MONTH'),(25,'SUBJECT'),(26,'PREPARE'),(27,'LOCK'),(28,'NDB'),(29,'CHECK'),(30,'FULL'),(31,'INT4'),(32,'BY'),(33,'NO'),(34,'MINUTE'),(35,'DATA'),(36,'DAY'),(37,'SHARE'),(38,'REAL'),(39,'SEPARATOR'),(40,'DELETE'),(41,'ON'),(42,'CONNECTION'),(43,'CLOSE'),(44,'X509'),(45,'USE'),(46,'WHERE'),(47,'PRIVILEGES'),(48,'SPATIAL'),(49,'SUPER'),(50,'SQL_BUFFER_RESULT'),(51,'IGNORE'),(52,'QUICK'),(53,'SIGNED'),(54,'SECURITY'),(55,'POLYGONFROMWKB'),(56,'NDBCLUSTER'),(57,'FALSE'),(58,'LEVEL'),(59,'FORCE'),(60,'BINARY'),(61,'TO'),(62,'CHANGE'),(63,'HOUR_MINUTE'),(64,'UPDATE'),(65,'INTO'),(66,'FEDERATED'),(67,'VARYING'),(68,'HOUR_SECOND'),(69,'VARIABLE'),(70,'ROLLBACK'),(71,'PROCEDURE'),(72,'RTREE'),(73,'TIMESTAMP'),(74,'IMPORT'),(75,'AGAINST'),(76,'CHECKSUM'),(77,'COUNT'),(78,'LONGBINARY'),(79,'THEN'),(80,'INSERT'),(81,'HANDLER'),(82,'ENGINES'),(83,'DAY_SECOND'),(84,'EXISTS'),(85,'RELEASE'),(86,'BOOLEAN'),(87,'MOD'),(88,'DEFAULT'),(89,'TYPE'),(90,'NO_WRITE_TO_BINLOG'),(91,'RESET'),(92,'DO'),(93,'ITERATE'),(94,'BIGINT'),(95,'SET'),(96,'ISSUER'),(97,'DATE'),(98,'STATUS'),(99,'FULLTEXT'),(100,'COMMENT'),(101,'MASTER_CONNECT_RETRY'),(102,'INNER'),(103,'STOP'),(104,'MASTER_LOG_FILE'),(105,'MRG_MYISAM'),(106,'PRECISION'),(107,'REQUIRE'),(108,'TRAILING'),(109,'LONG'),(110,'OPTION'),(111,'ELSE'),(112,'DEALLOCATE'),(113,'IO_THREAD'),(114,'CASE'),(115,'CIPHER'),(116,'CONTINUE'),(117,'FROM'),(118,'READ'),(119,'LEFT'),(120,'ELSEIF'),(121,'MINUTE_SECOND'),(122,'COMPACT'),(123,'DEC'),(124,'FOR'),(125,'WARNINGS'),(126,'MIN_ROWS'),(127,'STRING'),(128,'CONDITION'),(129,'FUNCTION'),(130,'ENCLOSED'),(131,'AGGREGATE'),(132,'FIELDS'),(133,'INT3'),(134,'ARCHIVE'),(135,'ADD'),(136,'AVG_ROW_LENGTH'),(137,'FLOAT4'),(138,'VIEW'),(139,'REPEATABLE'),(140,'INFILE'),(141,'ORDER'),(142,'USING'),(143,'MIDDLEINT'),(144,'GRANT'),(145,'UNSIGNED'),(146,'DECIMAL'),(147,'GEOMETRYFROMTEXT'),(148,'INDEXES'),(149,'FOREIGN'),(150,'CACHE'),(151,'HOSTS'),(152,'COMMIT'),(153,'SCHEMAS'),(154,'LEADING'),(155,'SNAPSHOT'),(156,'DECLARE'),(157,'LOAD'),(158,'SQL_CACHE'),(159,'CONVERT'),(160,'DYNAMIC'),(161,'POLYGONFROMTEXT'),(162,'BYTE'),(163,'LINESTRINGFROMWKB'),(164,'GLOBAL'),(165,'BERKELEYDB'),(166,'WHEN'),(167,'HAVING'),(168,'AS'),(169,'STARTING'),(170,'RELOAD'),(171,'AUTOCOMMIT'),(172,'REVOKE'),(173,'GRANTS'),(174,'OUTER'),(175,'FLOOR'),(176,'WITH'),(177,'STD'),(178,'AFTER'),(179,'CSV'),(180,'DISABLE'),(181,'OUTFILE'),(182,'LOW_PRIORITY'),(183,'FILE'),(184,'BDB'),(185,'SCHEMA'),(186,'SONAME'),(187,'POW'),(188,'MULTIPOINTFROMWKB'),(189,'INDEX'),(190,'MULTIPOINTFROMTEXT'),(191,'BACKUP'),(192,'MULTILINESTRINGFROMWKB'),(193,'EXTENDED'),(194,'CROSS'),(195,'NATIONAL'),(196,'GROUP'),(197,'UNDO'),(198,'ZEROFILL'),(199,'CLIENT'),(200,'MASTER_PASSWORD'),(201,'RELAY_LOG_FILE'),(202,'TRUE'),(203,'CHARACTER'),(204,'MASTER_USER'),(205,'ENGINE'),(206,'TABLE'),(207,'INSERT_METHOD'),(208,'CASCADE'),(209,'RELAY_LOG_POS'),(210,'SQL_CALC_FOUND_ROWS'),(211,'MYISAM'),(212,'LEAVE'),(213,'MODIFY'),(214,'MATCH'),(215,'MASTER_LOG_POS'),(216,'DESC'),(217,'DISTINCTROW'),(218,'TIME'),(219,'NUMERIC'),(220,'EXPANSION'),(221,'CURSOR'),(222,'GEOMETRYCOLLECTIONFROMTEXT'),(223,'CHAIN'),(224,'FLUSH'),(225,'CREATE'),(226,'ISAM'),(227,'MAX_UPDATES_PER_HOUR'),(228,'INT2'),(229,'PROCESSLIST'),(230,'LOGS'),(231,'HEAP'),(232,'SOUNDS'),(233,'BETWEEN'),(234,'MULTILINESTRINGFROMTEXT'),(235,'PACK_KEYS'),(236,'CALL'),(237,'FAST'),(238,'VALUES'),(239,'LOOP'),(240,'VARCHARACTER'),(241,'BEFORE'),(242,'SHOW'),(243,'REDUNDANT'),(244,'ALL'),(245,'USER_RESOURCES'),(246,'PARTIAL'),(247,'BINLOG'),(248,'END'),(249,'SECOND'),(250,'AND'),(251,'FLOAT8'),(252,'PREV'),(253,'HOUR'),(254,'SELECT'),(255,'DATABASES'),(256,'OR'),(257,'IDENTIFIED'),(258,'MASTER_SSL_CIPHER'),(259,'SQL_SLAVE_SKIP_COUNTER'),(260,'BOTH'),(261,'BOOL'),(262,'YEAR'),(263,'MASTER_PORT'),(264,'CONCURRENT'),(265,'UNIQUE'),(266,'TRIGGERS'),(267,'PROCESS'),(268,'CONSISTENT'),(269,'MASTER_SSL'),(270,'DATE_ADD'),(271,'MAX_CONNECTIONS_PER_HOUR'),(272,'LIKE'),(273,'FETCH'),(274,'IN'),(275,'COLUMN'),(276,'DUMPFILE'),(277,'USAGE'),(278,'EXECUTE'),(279,'MEMORY'),(280,'CEIL'),(281,'QUERY'),(282,'MASTER_HOST'),(283,'LINES'),(284,'SQL_THREAD'),(285,'MAX_QUERIES_PER_HOUR'),(286,'MULTIPOLYGONFROMWKB'),(287,'MASTER_SSL_CERT'),(288,'DAY_MINUTE'),(289,'TRANSACTION'),(290,'DATE_SUB'),(291,'GEOMETRYFROMWKB'),(292,'RENAME'),(293,'INT1'),(294,'ALTER'),(295,'MAX_ROWS'),(296,'RIGHT'),(297,'STRAIGHT_JOIN'),(298,'NATURAL'),(299,'VARIABLES'),(300,'ESCAPED'),(301,'SHA1'),(302,'PASSWORD'),(303,'CHAR'),(304,'OFFSET'),(305,'NEXT'),(306,'SQL_LOG_BIN'),(307,'ERRORS'),(308,'TEMPORARY'),(309,'SQL_SMALL_RESULT'),(310,'COMMITTED'),(311,'UPGRADE'),(312,'DELAY_KEY_WRITE'),(313,'BEGIN'),(314,'MEDIUM'),(315,'INTERVAL'),(316,'SSL'),(317,'DAY_HOUR'),(318,'REFERENCES'),(319,'AES_ENCRYPT'),(320,'STORAGE'),(321,'ISOLATION'),(322,'INT8'),(323,'RESTRICT'),(324,'LINESTRINGFROMTEXT'),(325,'IS'),(326,'UNCOMMITTED'),(327,'NOT'),(328,'DES_KEY_FILE'),(329,'COMPRESSED'),(330,'START'),(331,'IF'),(332,'SAVEPOINT'),(333,'PRIMARY'),(334,'INNOBASE'),(335,'LAST'),(336,'EXIT'),(337,'KEYS'),(338,'LIMIT'),(339,'KEY'),(340,'MERGE'),(341,'UNTIL'),(342,'SQL_NO_CACHE'),(343,'DELAYED'),(344,'CONSTRAINT'),(345,'SERIAL'),(346,'ACTION'),(347,'WRITE'),(348,'SESSION'),(349,'DATABASE'),(350,'NULL'),(351,'USE_FRM'),(352,'SLAVE'),(353,'TERMINATED'),(354,'ASC'),(355,'ENABLE'),(356,'OPTIONALLY'),(357,'DIRECTORY'),(358,'WHILE'),(359,'MAX_USER_CONNECTIONS'),(360,'DISTINCT'),(361,'LOCAL'),(362,'MASTER_SSL_KEY'),(363,'NONE'),(364,'TABLES'),(365,'<>'),(366,'RLIKE'),(367,'TRIGGER'),(368,'COLLATION'),(369,'SHUTDOWN'),(370,'HIGH_PRIORITY'),(371,'BTREE'),(372,'FIRST'),(373,'TYPES'),(374,'MASTER'),(375,'FIXED'),(376,'MULTIPOLYGONFROMTEXT'),(377,'ROW_FORMAT');
/*!40000 ALTER TABLE `help_keyword` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `help_relation`
--

DROP TABLE IF EXISTS `help_relation`;
CREATE TABLE `help_relation` (
  `help_topic_id` int(10) unsigned NOT NULL,
  `help_keyword_id` int(10) unsigned NOT NULL,
  PRIMARY KEY  (`help_keyword_id`,`help_topic_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='keyword-topic relation';

--
-- Dumping data for table `help_relation`
--

LOCK TABLES `help_relation` WRITE;
/*!40000 ALTER TABLE `help_relation` DISABLE KEYS */;
INSERT INTO `help_relation` VALUES (324,0),(204,1),(402,2),(382,3),(185,4),(165,5),(387,6),(17,7),(315,7),(124,8),(343,9),(73,10),(324,10),(12,11),(88,11),(112,11),(315,11),(185,12),(450,12),(346,13),(214,14),(90,15),(324,16),(25,17),(72,17),(166,17),(209,17),(234,17),(246,17),(369,17),(376,17),(417,17),(102,18),(26,19),(231,20),(86,21),(177,22),(315,23),(364,23),(422,23),(26,24),(177,25),(29,26),(209,26),(324,27),(422,28),(422,29),(17,30),(263,30),(315,30),(407,30),(422,30),(450,31),(41,32),(69,32),(177,32),(324,32),(330,32),(382,32),(417,32),(422,32),(422,33),(426,33),(26,34),(98,35),(382,35),(422,35),(26,36),(324,37),(185,38),(283,38),(330,39),(422,40),(426,40),(0,41),(426,41),(422,42),(44,43),(88,43),(177,44),(0,45),(41,46),(69,46),(88,46),(170,47),(177,47),(220,47),(187,48),(417,48),(177,49),(324,50),(0,51),(69,51),(86,51),(324,51),(382,51),(417,51),(41,52),(377,52),(420,52),(343,53),(177,54),(75,55),(435,55),(422,56),(350,57),(402,58),(0,59),(228,60),(268,60),(343,60),(387,60),(165,61),(414,61),(418,61),(165,62),(417,62),(26,63),(86,64),(324,64),(426,64),(36,65),(86,65),(273,65),(324,65),(422,66),(228,67),(26,68),(109,69),(124,70),(414,70),(13,71),(270,71),(297,71),(315,71),(324,71),(376,71),(396,71),(187,72),(81,73),(167,73),(382,74),(73,75),(422,76),(56,77),(298,77),(390,77),(255,78),(23,79),(70,79),(379,79),(86,80),(171,80),(439,80),(282,81),(251,82),(315,82),(26,83),(25,84),(133,84),(246,84),(124,85),(19,86),(73,86),(152,87),(86,88),(175,88),(214,88),(417,88),(422,88),(417,89),(422,89),(95,90),(296,90),(420,90),(424,90),(31,91),(129,91),(235,91),(446,92),(104,93),(196,94),(36,95),(69,95),(117,95),(124,95),(162,95),(188,95),(302,95),(417,95),(426,95),(444,95),(177,96),(26,97),(110,97),(233,97),(343,97),(48,98),(115,98),(190,98),(198,98),(297,98),(315,98),(334,98),(364,98),(187,99),(417,99),(422,99),(422,100),(165,101),(0,102),(45,103),(165,104),(422,105),(283,106),(177,107),(410,108),(255,109),(177,110),(70,111),(379,111),(209,112),(45,113),(294,113),(70,114),(379,114),(177,115),(282,116),(41,117),(98,117),(102,117),(315,117),(324,117),(329,117),(410,117),(30,118),(88,118),(402,118),(0,119),(23,120),(26,121),(422,122),(184,123),(159,124),(282,124),(315,124),(324,124),(380,124),(298,125),(315,125),(422,126),(185,127),(159,128),(13,129),(185,129),(270,129),(297,129),(315,129),(369,129),(376,129),(396,129),(382,130),(185,131),(315,132),(382,132),(223,133),(422,134),(50,135),(417,135),(417,136),(422,136),(147,137),(25,138),(137,138),(402,139),(382,140),(41,141),(69,141),(324,141),(330,141),(417,141),(0,142),(41,142),(71,142),(223,143),(177,144),(19,145),(108,145),(147,145),(184,145),(283,145),(343,145),(450,145),(134,146),(185,146),(373,147),(315,148),(417,149),(422,149),(426,149),(84,150),(129,150),(273,150),(123,151),(315,151),(124,152),(138,153),(315,153),(410,154),(124,155),(159,156),(175,156),(282,156),(380,156),(98,157),(273,157),(329,157),(382,157),(324,158),(343,159),(422,160),(359,161),(419,162),(406,163),(109,164),(115,164),(162,164),(318,164),(402,164),(422,165),(70,166),(379,166),(324,167),(0,168),(30,168),(324,168),(382,169),(177,170),(124,171),(220,172),(169,173),(315,173),(0,174),(196,175),(73,176),(177,176),(370,177),(417,178),(382,179),(422,179),(417,180),(324,181),(30,182),(36,182),(41,182),(69,182),(86,182),(382,182),(177,183),(144,184),(422,184),(133,185),(166,185),(188,185),(278,185),(315,185),(185,186),(436,187),(416,188),(0,189),(50,189),(72,189),(84,189),(187,189),(273,189),(277,189),(315,189),(417,189),(422,189),(384,190),(326,191),(242,192),(420,193),(0,194),(228,195),(387,195),(324,196),(282,197),(19,198),(108,198),(147,198),(184,198),(283,198),(450,198),(177,199),(165,200),(165,201),(350,202),(188,203),(228,203),(302,203),(387,203),(165,204),(315,205),(334,205),(417,205),(422,205),(50,206),(190,206),(246,206),(247,206),(315,206),(326,206),(329,206),(422,207),(25,208),(246,208),(422,208),(426,208),(165,209),(324,210),(422,211),(279,212),(417,213),(73,214),(165,215),(299,216),(324,216),(330,216),(324,217),(284,218),(342,218),(343,218),(184,219),(73,220),(380,221),(217,222),(124,223),(129,224),(13,225),(16,225),(50,225),(133,225),(185,225),(187,225),(247,225),(270,225),(278,225),(315,225),(422,225),(422,226),(177,227),(205,228),(315,229),(407,229),(144,230),(268,230),(315,230),(334,230),(422,231),(344,232),(125,233),(89,234),(422,235),(307,236),(377,237),(36,238),(312,239),(228,240),(418,241),(13,242),(17,242),(20,242),(48,242),(56,242),(102,242),(112,242),(115,242),(123,242),(138,242),(144,242),(169,242),(170,242),(190,242),(198,242),(247,242),(251,242),(263,242),(268,242),(277,242),(278,242),(297,242),(298,242),(302,242),(318,242),(334,242),(364,242),(407,242),(442,242),(422,243),(177,244),(220,244),(274,244),(324,244),(296,245),(422,246),(102,247),(23,248),(70,248),(204,248),(295,248),(312,248),(379,248),(446,248),(26,249),(125,250),(285,250),(283,251),(88,252),(26,253),(36,254),(227,254),(231,254),(138,255),(315,255),(119,256),(177,257),(165,258),(162,259),(410,260),(19,261),(92,261),(26,262),(165,263),(382,264),(417,265),(20,266),(177,267),(124,268),(165,269),(26,270),(177,271),(315,272),(344,272),(349,273),(73,274),(102,274),(324,274),(417,275),(324,276),(177,277),(71,278),(177,278),(324,279),(403,280),(73,281),(129,281),(165,282),(382,283),(45,284),(294,284),(177,285),(103,286),(165,287),(26,288),(124,289),(402,289),(26,290),(122,291),(417,292),(19,293),(50,294),(137,294),(177,294),(396,294),(417,294),(422,295),(0,296),(0,297),(324,297),(0,298),(315,299),(318,299),(382,300),(254,301),(177,302),(343,303),(419,303),(324,304),(88,305),(444,306),(56,307),(315,307),(246,308),(324,309),(402,310),(377,311),(422,312),(124,313),(295,313),(377,314),(26,315),(177,316),(26,317),(177,318),(422,318),(426,318),(447,319),(251,320),(402,321),(108,322),(25,323),(246,323),(426,323),(47,324),(337,325),(402,326),(133,327),(281,327),(296,328),(422,329),(124,330),(294,330),(23,331),(25,331),(133,331),(166,331),(246,331),(433,331),(414,332),(417,333),(422,334),(88,335),(282,336),(277,337),(315,337),(417,337),(41,338),(69,338),(88,338),(102,338),(324,338),(50,339),(86,339),(417,339),(422,339),(426,339),(422,340),(204,341),(324,342),(36,343),(86,343),(439,343),(417,344),(422,344),(214,345),(422,345),(422,346),(426,346),(30,347),(109,348),(115,348),(318,348),(402,348),(133,349),(166,349),(278,349),(315,349),(337,350),(426,350),(420,351),(31,352),(45,352),(123,352),(198,352),(294,352),(382,353),(324,354),(330,354),(417,355),(382,356),(422,357),(446,358),(177,359),(258,360),(274,360),(324,360),(330,360),(351,360),(390,360),(430,360),(30,361),(95,361),(296,361),(382,361),(420,361),(424,361),(165,362),(177,363),(30,364),(112,364),(263,364),(315,364),(445,365),(22,366),(16,367),(234,367),(442,368),(177,369),(86,370),(324,370),(187,371),(88,372),(417,372),(422,372),(315,373),(48,374),(98,374),(165,374),(235,374),(268,374),(329,374),(184,375),(422,375),(176,376),(422,377);
/*!40000 ALTER TABLE `help_relation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `help_topic`
--

DROP TABLE IF EXISTS `help_topic`;
CREATE TABLE `help_topic` (
  `help_topic_id` int(10) unsigned NOT NULL,
  `name` char(64) NOT NULL,
  `help_category_id` smallint(5) unsigned NOT NULL,
  `description` text NOT NULL,
  `example` text NOT NULL,
  `url` char(128) NOT NULL,
  PRIMARY KEY  (`help_topic_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='help topics';

--
-- Dumping data for table `help_topic`
--

LOCK TABLES `help_topic` WRITE;
/*!40000 ALTER TABLE `help_topic` DISABLE KEYS */;
INSERT INTO `help_topic` VALUES (0,'JOIN',25,'MySQL supports the following JOIN syntaxes for the table_references\npart of SELECT statements and multiple-table DELETE and UPDATE\nstatements:\n\ntable_references:\n    table_reference [, table_reference] ...\n\ntable_reference:\n    table_factor\n  | join_table\n\ntable_factor:\n    tbl_name [[AS] alias]\n        [{USE|IGNORE|FORCE} INDEX (key_list)]\n  | ( table_references )\n  | { OJ table_reference LEFT OUTER JOIN table_reference\n        ON conditional_expr }\n\njoin_table:\n    table_reference [INNER | CROSS] JOIN table_factor [join_condition]\n  | table_reference STRAIGHT_JOIN table_factor\n  | table_reference STRAIGHT_JOIN table_factor ON condition\n  | table_reference LEFT [OUTER] JOIN table_reference join_condition\n  | table_reference NATURAL [LEFT [OUTER]] JOIN table_factor\n  | table_reference RIGHT [OUTER] JOIN table_reference join_condition\n  | table_reference NATURAL [RIGHT [OUTER]] JOIN table_factor\n\njoin_condition:\n    ON conditional_expr\n  | USING (column_list)\n\nA table reference is also known as a join expression.\n\nThe syntax of table_factor is extended in comparison with the SQL\nStandard. The latter accepts only table_reference, not a list of them\ninside a pair of parentheses.\n\nThis is a conservative extension if we consider each comma in a list of\ntable_reference items as equivalent to an inner join. For example:\n\nSELECT * FROM t1 LEFT JOIN (t2, t3, t4)\n                 ON (t2.a=t1.a AND t3.b=t1.b AND t4.c=t1.c)\n\nis equivalent to:\n\nSELECT * FROM t1 LEFT JOIN (t2 CROSS JOIN t3 CROSS JOIN t4)\n                 ON (t2.a=t1.a AND t3.b=t1.b AND t4.c=t1.c)\n\nIn MySQL, CROSS JOIN is a syntactic equivalent to INNER JOIN (they can\nreplace each other. In standard SQL, they are not equivalent. INNER\nJOIN is used with an ON clause, CROSS JOIN is used otherwise.\n\nIn versions of MySQL prior to 5.0.1, parentheses in table_references\nwere just omitted and all join operations were grouped to the left. In\ngeneral, parentheses can be ignored in join expressions containing only\ninner join operations. As of 5.0.1, nested joins are allowed (see\n[nested-joins]).\n\nFurther changes in join processing were made in 5.0.12 to make MySQL\nmore compliant with standard SQL. These charges are described later in\nthis section.\n','SELECT table1.* FROM table1\n  LEFT JOIN table2 ON table1.id=table2.id\n  WHERE table2.id IS NULL;\n','join'),(1,'HEX',33,'Syntax:\nHEX(N_or_S)\n\nIf N_or_S is a number, returns a string representation of the\nhexadecimal value of N, where N is a longlong (BIGINT) number. This is\nequivalent to CONV(N,10,16).\n\nIf N_or_S is a string, returns a hexadecimal string representation of\nN_or_S where each character in N_or_S is converted to two hexadecimal\ndigits.\n','mysql> SELECT HEX(255);\n        -> \'FF\'\nmysql> SELECT 0x616263;\n        -> \'abc\'\nmysql> SELECT HEX(\'abc\');\n        -> 616263\n','string-functions'),(2,'REPLACE',33,'Syntax:\nREPLACE(str,from_str,to_str)\n\nReturns the string str with all occurrences of the string from_str\nreplaced by the string to_str. REPLACE() performs a case-sensitive\nmatch when searching for from_str.\n','mysql> SELECT REPLACE(\'www.mysql.com\', \'w\', \'Ww\');\n        -> \'WwWwWw.mysql.com\'\n','string-functions'),(3,'CONTAINS',26,'Contains(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 completely contains g2.\n','','functions-that-test-spatial-relationships-between-geometries'),(4,'SRID',32,'SRID(g)\n\nReturns an integer indicating the Spatial Reference System ID for the\ngeometry value g.\n\nIn MySQL, the SRID value is just an integer associated with the\ngeometry value. All calculations are done assuming Euclidean (planar)\ngeometry.\n','mysql> SELECT SRID(GeomFromText(\'LineString(1 1,2 2)\',101));\n+-----------------------------------------------+\n| SRID(GeomFromText(\'LineString(1 1,2 2)\',101)) |\n+-----------------------------------------------+\n|                                           101 |\n+-----------------------------------------------+\n','general-geometry-property-functions'),(5,'CURRENT_TIMESTAMP',28,'Syntax:\nCURRENT_TIMESTAMP, CURRENT_TIMESTAMP()\n\nCURRENT_TIMESTAMP and CURRENT_TIMESTAMP() are synonyms for NOW().\n','','date-and-time-functions'),(6,'VARIANCE',14,'Syntax:\nVARIANCE(expr)\n\nReturns the population standard variance of expr. This is an extension\nto standard SQL. As of MySQL 5.0.3, the standard SQL function VAR_POP()\ncan be used instead.\n\nVARIANCE() returns NULL if there were no matching rows.\n','','group-by-functions'),(7,'VAR_SAMP',14,'Syntax:\nVAR_SAMP(expr)\n\nReturns the sample variance of expr. That is, the denominator is the\nnumber of rows minus one. This function was added in MySQL 5.0.3.\n\nVAR_SAMP() returns NULL if there were no matching rows.\n','','group-by-functions'),(8,'CONCAT',33,'Syntax:\nCONCAT(str1,str2,...)\n\nReturns the string that results from concatenating the arguments. May\nhave one or more arguments. If all arguments are non-binary strings,\nthe result is a non-binary string. If the arguments include any binary\nstrings, the result is a binary string. A numeric argument is converted\nto its equivalent binary string form; if you want to avoid that, you\ncan use an explicit type cast, as in this example:\n\nSELECT CONCAT(CAST(int_col AS CHAR), char_col);\n\nCONCAT() returns NULL if any argument is NULL.\n','mysql> SELECT CONCAT(\'My\', \'S\', \'QL\');\n        -> \'MySQL\'\nmysql> SELECT CONCAT(\'My\', NULL, \'QL\');\n        -> NULL\nmysql> SELECT CONCAT(14.3);\n        -> \'14.3\'\n','string-functions'),(9,'GEOMETRY HIERARCHY',30,'Geometry is the base class. It is an abstract class. The instantiable\nsubclasses of Geometry are restricted to zero-, one-, and\ntwo-dimensional geometric objects that exist in two-dimensional\ncoordinate space. All instantiable geometry classes are defined so that\nvalid instances of a geometry class are topologically closed (that is,\nall defined geometries include their boundary).\n\nThe base Geometry class has subclasses for Point, Curve, Surface, and\nGeometryCollection:\n\no Point represents zero-dimensional objects.\n\no Curve represents one-dimensional objects, and has subclass\n  LineString, with sub-subclasses Line and LinearRing.\n\no Surface is designed for two-dimensional objects and has subclass\n  Polygon.\n\no GeometryCollection has specialized zero-, one-, and two-dimensional\n  collection classes named MultiPoint, MultiLineString, and\n  MultiPolygon for modeling geometries corresponding to collections of\n  Points, LineStrings, and Polygons, respectively. MultiCurve and\n  MultiSurface are introduced as abstract superclasses that generalize\n  the collection interfaces to handle Curves and Surfaces.\n\nGeometry, Curve, Surface, MultiCurve, and MultiSurface are defined as\nnon-instantiable classes. They define a common set of methods for their\nsubclasses and are included for extensibility.\n\nPoint, LineString, Polygon, GeometryCollection, MultiPoint,\nMultiLineString, and MultiPolygon are instantiable classes.\n','','gis-geometry-class-hierarchy'),(10,'CHAR FUNCTION',33,'Syntax:\nCHAR(N,... [USING charset_name])\n\nCHAR() interprets each argument N as an integer and returns a string\nconsisting of the characters given by the code values of those\nintegers. NULL values are skipped.\nAs of MySQL 5.0.15, CHAR() arguments larger than 255 are converted into\nmultiple result bytes. For example, CHAR(256) is equivalent to\nCHAR(1,0), and CHAR(256*256) is equivalent to CHAR(1,0,0):\n\nmysql> SELECT HEX(CHAR(1,0)), HEX(CHAR(256));\n+----------------+----------------+\n| HEX(CHAR(1,0)) | HEX(CHAR(256)) |\n+----------------+----------------+\n| 0100           | 0100           |\n+----------------+----------------+\nmysql> SELECT HEX(CHAR(1,0,0)), HEX(CHAR(256*256));\n+------------------+--------------------+\n| HEX(CHAR(1,0,0)) | HEX(CHAR(256*256)) |\n+------------------+--------------------+\n| 010000           | 010000             |\n+------------------+--------------------+\n\nBy default, CHAR() returns a binary string. To produce a string in a\ngiven character set, use the optional USING clause:\n\nmysql> SELECT CHARSET(CHAR(0x65)), CHARSET(CHAR(0x65 USING utf8));\n+---------------------+--------------------------------+\n| CHARSET(CHAR(0x65)) | CHARSET(CHAR(0x65 USING utf8)) |\n+---------------------+--------------------------------+\n| binary              | utf8                           |\n+---------------------+--------------------------------+\n\nIf USING is given and the result string is illegal for the given\ncharacter set, a warning is issued. Also, if strict SQL mode is\nenabled, the result from CHAR() becomes NULL.\n\nBefore MySQL 5.0.15, CHAR() returns a string in the connection\ncharacter set and the USING clause is unavailable. In addition, each\nargument is interpreted modulo 256, so CHAR(256) and CHAR(256*256) both\nare equivalent to CHAR(0).\n','mysql> SELECT CHAR(77,121,83,81,\'76\');\n        -> \'MySQL\'\nmysql> SELECT CHAR(77,77.3,\'77.3\');\n        -> \'MMM\'\n','string-functions'),(11,'DATETIME',20,'DATETIME\n\nA date and time combination. The supported range is \'1000-01-01\n00:00:00\' to \'9999-12-31 23:59:59\'. MySQL displays DATETIME values in\n\'YYYY-MM-DD HH:MM:SS\' format, but allows you to assign values to\nDATETIME columns using either strings or numbers.\n','','date-and-time-type-overview'),(12,'OPEN',35,'Syntax:\nOPEN cursor_name\n\nThis statement opens a previously declared cursor.\n','','open'),(13,'SHOW CREATE PROCEDURE',25,'Syntax:\nSHOW CREATE {PROCEDURE | FUNCTION} sp_name\n\nThis statement is a MySQL extension. Similar to SHOW CREATE TABLE, it\nreturns the exact string that can be used to re-create the named\nroutine.\n','mysql> SHOW CREATE FUNCTION test.hello\\G\n*************************** 1. row ***************************\n       Function: hello\n       sql_mode:\nCreate Function: CREATE FUNCTION `test`.`hello`(s CHAR(20)) RETURNS CHAR(50)\n                 RETURN CONCAT(\'Hello, \',s,\'!\')\n','show-create-procedure'),(14,'INTEGER',20,'INTEGER[(M)] [UNSIGNED] [ZEROFILL]\n\nThis type is a synonym for INT.\n','','numeric-type-overview'),(15,'LOWER',33,'Syntax:\nLOWER(str)\n\nReturns the string str with all characters changed to lowercase\naccording to the current character set mapping. The default is latin1\n(cp1252 West European).\n','mysql> SELECT LOWER(\'QUADRATICALLY\');\n        -> \'quadratically\'\n','string-functions'),(16,'CREATE TRIGGER',21,'Syntax:\nCREATE\n    [DEFINER = { user | CURRENT_USER }]\n    TRIGGER trigger_name trigger_time trigger_event\n    ON tbl_name FOR EACH ROW trigger_stmt\n\nThis statement creates a new trigger. A trigger is a named database\nobject that is associated with a table, and that activates when a\nparticular event occurs for the table. CREATE TRIGGER was added in\nMySQL 5.0.2. Currently, its use requires the SUPER privilege.\n\nThe trigger becomes associated with the table named tbl_name, which\nmust refer to a permanent table. You cannot associate a trigger with a\nTEMPORARY table or a view.\n\nWhen the trigger is activated, the DEFINER clause determines the\nprivileges that apply, as described later in this section.\n\ntrigger_time is the trigger action time. It can be BEFORE or AFTER to\nindicate that the trigger activates before or after the statement that\nactivated it.\n\ntrigger_event indicates the kind of statement that activates the\ntrigger. The trigger_event can be one of the following:\n\no INSERT: The trigger is activated whenever a new row is inserted into\n  the table; for example, through INSERT, LOAD DATA, and REPLACE\n  statements.\n\no UPDATE: The trigger is activated whenever a row is modified; for\n  example, through UPDATE statements.\n\no DELETE: The trigger is activated whenever a row is deleted from the\n  table; for example, through DELETE and REPLACE statements. However, a\n  TRUNCATE statement on the table does not invoke this trigger. See\n  [truncate].\n','','create-trigger'),(17,'SHOW COLUMNS',25,'Syntax:\nSHOW [FULL] COLUMNS FROM tbl_name [FROM db_name] [LIKE \'pattern\']\n\nSHOW COLUMNS displays information about the columns in a given table.\nIt also works for views as of MySQL 5.0.1.\n\nIf the data types differ from what you expect them to be based on your\nCREATE TABLE statement, note that MySQL sometimes changes data types\nwhen you create or alter a table. The conditions for which this occurs\nare described in [silent-column-changes].\n\nThe FULL keyword causes the output to include the privileges you have\nas well as any per-column comments for each column.\n\nYou can use db_name.tbl_name as an alternative to the tbl_name FROM\ndb_name syntax. In other words, these two statements are equivalent:\n\nmysql> SHOW COLUMNS FROM mytable FROM mydb;\nmysql> SHOW COLUMNS FROM mydb.mytable;\n\nSHOW FIELDS is a synonym for SHOW COLUMNS. You can also list a table\'s\ncolumns with the mysqlshow db_name tbl_name command.\n\nThe DESCRIBE statement provides information similar to SHOW COLUMNS.\nSee [describe].\n','','show-columns'),(18,'MONTH',28,'Syntax:\nMONTH(date)\n\nReturns the month for date, in the range 0 to 12.\n','mysql> SELECT MONTH(\'1998-02-03\');\n        -> 2\n','date-and-time-functions'),(19,'TINYINT',20,'TINYINT[(M)] [UNSIGNED] [ZEROFILL]\n\nA very small integer. The signed range is -128 to 127. The unsigned\nrange is 0 to 255.\n','','numeric-type-overview'),(20,'SHOW TRIGGERS',25,'Syntax:\nSHOW TRIGGERS [FROM db_name] [LIKE expr]\n\nSHOW TRIGGERS lists the triggers currently defined on the MySQL server.\nThis statement requires the SUPER privilege. It was implemented in\nMySQL 5.0.10.\n\nFor the trigger ins_sum as defined in [using-triggers], the output of\nthis statement is as shown here:\n\nmysql> SHOW TRIGGERS LIKE \'acc%\'\\G\n*************************** 1. row ***************************\n  Trigger: ins_sum\n    Event: INSERT\n    Table: account\nStatement: SET @sum = @sum + NEW.amount\n   Timing: BEFORE\n  Created: NULL\n sql_mode:\n  Definer: myname@localhost\n','','show-triggers'),(21,'MASTER_POS_WAIT',13,'Syntax:\nMASTER_POS_WAIT(log_name,log_pos[,timeout])\n\nThis function is useful for control of master/slave synchronization. It\nblocks until the slave has read and applied all updates up to the\nspecified position in the master log. The return value is the number of\nlog events the slave had to wait for to advance to the specified\nposition. The function returns NULL if the slave SQL thread is not\nstarted, the slave\'s master information is not initialized, the\narguments are incorrect, or an error occurs. It returns -1 if the\ntimeout has been exceeded. If the slave SQL thread stops while\nMASTER_POS_WAIT() is waiting, the function returns NULL. If the slave\nis past the specified position, the function returns immediately.\n','','miscellaneous-functions'),(22,'REGEXP',33,'Syntax:\nexpr REGEXP pat expr RLIKE pat\n\nPerforms a pattern match of a string expression expr against a pattern\npat. The pattern can be an extended regular expression. The syntax for\nregular expressions is discussed in [regexp]. Returns 1 if expr matches\npat; otherwise it returns 0. If either expr or pat is NULL, the result\nis NULL. RLIKE is a synonym for REGEXP, provided for mSQL\ncompatibility.\n\nThe pattern need not be a literal string. For example, it can be\nspecified as a string expression or table column.\n\nNote: Because MySQL uses the C escape syntax in strings (for example,\n`\\n\' to represent the newline character), you must double any `\\\' that\nyou use in your REGEXP strings.\n\nREGEXP is not case sensitive, except when used with binary strings.\n','mysql> SELECT \'Monty!\' REGEXP \'m%y%%\';\n        -> 0\nmysql> SELECT \'Monty!\' REGEXP \'.*\';\n        -> 1\nmysql> SELECT \'new*\\n*line\' REGEXP \'new\\\\*.\\\\*line\';\n        -> 1\nmysql> SELECT \'a\' REGEXP \'A\', \'a\' REGEXP BINARY \'A\';\n        -> 1  0\nmysql> SELECT \'a\' REGEXP \'^[a-d]\';\n        -> 1\n','string-comparison-functions'),(23,'IF STATEMENT',35,'Syntax:\nIF search_condition THEN statement_list\n    [ELSEIF search_condition THEN statement_list] ...\n    [ELSE statement_list]\nEND IF\n\nIF implements a basic conditional construct. If the search_condition\nevaluates to true, the corresponding SQL statement list is executed. If\nno search_condition matches, the statement list in the ELSE clause is\nexecuted. Each statement_list consists of one or more statements.\n\nNote: There is also an IF() function, which differs from the IF\nstatement described here. See [control-flow-functions].\n','','if-statement'),(24,'^',18,'Syntax:\n^\n\nBitwise XOR:\n','mysql> SELECT 1 ^ 1;\n        -> 0\nmysql> SELECT 1 ^ 0;\n        -> 1\nmysql> SELECT 11 ^ 3;\n        -> 8\n','bit-functions'),(25,'DROP VIEW',36,'Syntax:\nDROP VIEW [IF EXISTS]\n    view_name [, view_name] ...\n    [RESTRICT | CASCADE]\n\nDROP VIEW removes one or more views. You must have the DROP privilege\nfor each view.\n\nThe IF EXISTS clause prevents an error from occurring for views that\ndon\'t exist. When this clause is given, a NOTE is generated for each\nnon-existent view. See [show-warnings].\n\nRESTRICT and CASCADE, if given, are parsed and ignored.\n','','drop-view'),(26,'DATE OPERATIONS',28,'Syntax:\nDATE_ADD(date,INTERVAL expr type), DATE_SUB(date,INTERVAL expr type)\n\nThese functions perform date arithmetic. date is a DATETIME or DATE\nvalue specifying the starting date. expr is an expression specifying\nthe interval value to be added or subtracted from the starting date.\nexpr is a string; it may start with a `-\' for negative intervals. type\nis a keyword indicating how the expression should be interpreted.\n','mysql> SELECT \'1997-12-31 23:59:59\' + INTERVAL 1 SECOND;\n        -> \'1998-01-01 00:00:00\'\nmysql> SELECT INTERVAL 1 DAY + \'1997-12-31\';\n        -> \'1998-01-01\'\nmysql> SELECT \'1998-01-01\' - INTERVAL 1 SECOND;\n        -> \'1997-12-31 23:59:59\'\nmysql> SELECT DATE_ADD(\'1997-12-31 23:59:59\',\n    ->                 INTERVAL 1 SECOND);\n        -> \'1998-01-01 00:00:00\'\nmysql> SELECT DATE_ADD(\'1997-12-31 23:59:59\',\n    ->                 INTERVAL 1 DAY);\n        -> \'1998-01-01 23:59:59\'\nmysql> SELECT DATE_ADD(\'1997-12-31 23:59:59\',\n    ->                 INTERVAL \'1:1\' MINUTE_SECOND);\n        -> \'1998-01-01 00:01:00\'\nmysql> SELECT DATE_SUB(\'1998-01-01 00:00:00\',\n    ->                 INTERVAL \'1 1:1:1\' DAY_SECOND);\n        -> \'1997-12-30 22:58:59\'\nmysql> SELECT DATE_ADD(\'1998-01-01 00:00:00\',\n    ->                 INTERVAL \'-1 10\' DAY_HOUR);\n        -> \'1997-12-30 14:00:00\'\nmysql> SELECT DATE_SUB(\'1998-01-02\', INTERVAL 31 DAY);\n        -> \'1997-12-02\'\nmysql> SELECT DATE_ADD(\'1992-12-31 23:59:59.000002\',\n    ->            INTERVAL \'1.999999\' SECOND_MICROSECOND);\n        -> \'1993-01-01 00:00:01.000001\'\n','date-and-time-functions'),(27,'WITHIN',26,'Within(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 is spatially within g2.\n','','functions-that-test-spatial-relationships-between-geometries'),(28,'WEEK',28,'Syntax:\nWEEK(date[,mode])\n\nThis function returns the week number for date. The two-argument form\nof WEEK() allows you to specify whether the week starts on Sunday or\nMonday and whether the return value should be in the range from 0 to 53\nor from 1 to 53. If the mode argument is omitted, the value of the\ndefault_week_format system variable is used. See\n[server-system-variables].\n','mysql> SELECT WEEK(\'1998-02-20\');\n        -> 7\nmysql> SELECT WEEK(\'1998-02-20\',0);\n        -> 7\nmysql> SELECT WEEK(\'1998-02-20\',1);\n        -> 8\nmysql> SELECT WEEK(\'1998-12-31\',1);\n        -> 53\n','date-and-time-functions'),(29,'PREPARE',25,'Syntax:\nPREPARE stmt_name FROM preparable_stmt\n\nThe PREPARE statement prepares a statement and assigns it a name,\nstmt_name, by which to refer to the statement later. Statement names\nare not case sensitive. preparable_stmt is either a string literal or a\nuser variable that contains the text of the statement. The text must\nrepresent a single SQL statement, not multiple statements. Within the\nstatement, `?\' characters can be used as parameter markers to indicate\nwhere data values are to be bound to the query later when you execute\nit. The `?\' characters should not be enclosed within quotes, even if\nyou intend to bind them to string values. Parameter markers can be used\nonly where data values should appear, not for SQL keywords,\nidentifiers, and so forth.\n\nIf a prepared statement with the given name already exists, it is\ndeallocated implicitly before the new statement is prepared. This means\nthat if the new statement contains an error and cannot be prepared, an\nerror is returned and no statement with the given name exists.\n\nThe scope of a prepared statement is the client session within which it\nis created. Other clients cannot see it.\n','','sqlps'),(30,'LOCK',7,'Syntax:\nLOCK TABLES\n    tbl_name [AS alias] {READ [LOCAL] | [LOW_PRIORITY] WRITE}\n    [, tbl_name [AS alias] {READ [LOCAL] | [LOW_PRIORITY] WRITE}] ...\nUNLOCK TABLES\n\nLOCK TABLES locks tables for the current thread. If any of the tables\nare locked by other threads, it blocks until all locks can be acquired.\nUNLOCK TABLES releases any locks held by the current thread. All tables\nthat are locked by the current thread are implicitly unlocked when the\nthread issues another LOCK TABLES, or when the connection to the server\nis closed.\n\nA table lock protects only against inappropriate reads or writes by\nother clients. The client holding the lock, even a read lock, can\nperform table-level operations such as DROP TABLE.\n','','lock-tables'),(31,'RESET SLAVE',25,'Syntax:\nRESET SLAVE\n\nRESET SLAVE makes the slave forget its replication position in the\nmaster\'s binary logs. This statement is meant to be used for a clean\nstart: It deletes the master.info and relay-log.info files, all the\nrelay logs, and starts a new relay log.\n\nNote: All relay logs are deleted, even if they have not been completely\nexecuted by the slave SQL thread. (This is a condition likely to exist\non a replication slave if you have issued a STOP SLAVE statement or if\nthe slave is highly loaded.)\n\nConnection information stored in the master.info file is immediately\nreset using any values specified in the corresponding startup options.\nThis information includes values such as master host, master port,\nmaster user, and master password. If the slave SQL thread was in the\nmiddle of replicating temporary tables when it was stopped, and RESET\nSLAVE is issued, these replicated temporary tables are deleted on the\nslave.\n','','reset-slave'),(32,'POLYGON',22,'Polygon(ls1,ls2,...)\n\nConstructs a WKB Polygon value from a number of WKB LineString\narguments. If any argument does not represent the WKB of a LinearRing\n(that is, not a closed and simple LineString) the return value is NULL.\n','','gis-mysql-specific-functions'),(33,'MINUTE',28,'Syntax:\nMINUTE(time)\n\nReturns the minute for time, in the range 0 to 59.\n','mysql> SELECT MINUTE(\'98-02-03 10:05:03\');\n        -> 5\n','date-and-time-functions'),(34,'DAY',28,'Syntax:\nDAY(date)\n\nDAY() is a synonym for DAYOFMONTH().\n','','date-and-time-functions'),(35,'MID',33,'Syntax:\nMID(str,pos,len)\n\nMID(str,pos,len) is a synonym for SUBSTRING(str,pos,len).\n','','string-functions'),(36,'REPLACE INTO',25,'Syntax:\nREPLACE [LOW_PRIORITY | DELAYED]\n    [INTO] tbl_name [(col_name,...)]\n    VALUES ({expr | DEFAULT},...),(...),...\n\nOr:\n\nREPLACE [LOW_PRIORITY | DELAYED]\n    [INTO] tbl_name\n    SET col_name={expr | DEFAULT}, ...\n\nOr:\n\nREPLACE [LOW_PRIORITY | DELAYED]\n    [INTO] tbl_name [(col_name,...)]\n    SELECT ...\n\nREPLACE works exactly like INSERT, except that if an old row in the\ntable has the same value as a new row for a PRIMARY KEY or a UNIQUE\nindex, the old row is deleted before the new row is inserted. See\n[insert].\n\nREPLACE is a MySQL extension to the SQL standard. It either inserts, or\ndeletes and inserts. If you\'re looking for a statement that follows the\nSQL standard, and that either inserts or updates, see\n[insert-on-duplicate].\n\nNote that unless the table has a PRIMARY KEY or UNIQUE index, using a\nREPLACE statement makes no sense. It becomes equivalent to INSERT,\nbecause there is no index to be used to determine whether a new row\nduplicates another.\n\nValues for all columns are taken from the values specified in the\nREPLACE statement. Any missing columns are set to their default values,\njust as happens for INSERT. You cannot refer to values from the current\nrow and use them in the new row. If you use an assignment such as SET\ncol_name = col_name + 1, the reference to the column name on the right\nhand side is treated as DEFAULT(col_name), so the assignment is\nequivalent to SET col_name = DEFAULT(col_name) + 1.\n\nTo use REPLACE, you must have both the INSERT and DELETE privileges for\nthe table.\n','','replace'),(37,'UUID',13,'Syntax:\nUUID()\n\nReturns a Universal Unique Identifier (UUID) generated according to\n\"DCE 1.1: Remote Procedure Call\" (Appendix A) CAE (Common Applications\nEnvironment) Specifications published by The Open Group in October 1997\n(Document Number C706,\nhttp://www.opengroup.org/public/pubs/catalog/c706.htm).\n\nA UUID is designed as a number that is globally unique in space and\ntime. Two calls to UUID() are expected to generate two different\nvalues, even if these calls are performed on two separate computers\nthat are not connected to each other.\n\nA UUID is a 128-bit number represented by a string of five hexadecimal\nnumbers in aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee format:\n\no The first three numbers are generated from a timestamp.\n\no The fourth number preserves temporal uniqueness in case the timestamp\n  value loses monotonicity (for example, due to daylight saving time).\n\no The fifth number is an IEEE 802 node number that provides spatial\n  uniqueness. A random number is substituted if the latter is not\n  available (for example, because the host computer has no Ethernet\n  card, or we do not know how to find the hardware address of an\n  interface on your operating system). In this case, spatial uniqueness\n  cannot be guaranteed. Nevertheless, a collision should have very low\n  probability.\n\n  Currently, the MAC address of an interface is taken into account only\n  on FreeBSD and Linux. On other operating systems, MySQL uses a\n  randomly generated 48-bit number.\n','mysql> SELECT UUID();\n        -> \'6ccd780c-baba-1026-9564-0040f4311e29\'\n','miscellaneous-functions'),(38,'LINESTRING',22,'LineString(pt1,pt2,...)\n\nConstructs a WKB LineString value from a number of WKB Point arguments.\nIf any argument is not a WKB Point, the return value is NULL. If the\nnumber of Point arguments is less than two, the return value is NULL.\n','','gis-mysql-specific-functions'),(39,'SLEEP',13,'Syntax:\nSLEEP(duration)\n\nSleeps (pauses) for the number of seconds given by the duration\nargument, then returns 0. If SLEEP() is interrupted, it returns 1. The\nduration may have a fractional part given in microseconds. This\nfunction was added in MySQL 5.0.12.\n','','miscellaneous-functions'),(40,'CONNECTION_ID',15,'Syntax:\nCONNECTION_ID()\n\nReturns the connection ID (thread ID) for the connection. Every\nconnection has an ID that is unique among the set of currently\nconnected clients.\n','mysql> SELECT CONNECTION_ID();\n        -> 23786\n','information-functions'),(41,'DELETE',25,'Syntax:\nSingle-table syntax:\n\nDELETE [LOW_PRIORITY] [QUICK] [IGNORE] FROM tbl_name\n    [WHERE where_condition]\n    [ORDER BY ...]\n    [LIMIT row_count]\n\nMultiple-table syntax:\n\nDELETE [LOW_PRIORITY] [QUICK] [IGNORE]\n    tbl_name[.*] [, tbl_name[.*]] ...\n    FROM table_references\n    [WHERE where_condition]\n\nOr:\n\nDELETE [LOW_PRIORITY] [QUICK] [IGNORE]\n    FROM tbl_name[.*] [, tbl_name[.*]] ...\n    USING table_references\n    [WHERE where_condition]\n\nFor the single-table syntax, the DELETE statement deletes rows from\ntbl_name and returns the number of rows deleted. The WHERE clause, if\ngiven, specifies the conditions that identify which rows to delete.\nWith no WHERE clause, all rows are deleted. If the ORDER BY clause is\nspecified, the rows are deleted in the order that is specified. The\nLIMIT clause places a limit on the number of rows that can be deleted.\n\nFor the multiple-table syntax, DELETE deletes from each tbl_name the\nrows that satisfy the conditions. In this case, ORDER BY and LIMIT\ncannot be used.\n\nwhere_condition is an expression that evaluates to true for each row to\nbe deleted. It is specified as described in [select].\n\nAs stated, a DELETE statement with no WHERE clause deletes all rows. A\nfaster way to do this, when you do not want to know the number of\ndeleted rows, is to use TRUNCATE TABLE. See [truncate].\n','','delete'),(42,'ROUND',4,'Syntax:\nROUND(X), ROUND(X,D)\n\nReturns the argument X, rounded to the nearest integer. With two\narguments, returns X rounded to D decimal places. D can be negative to\ncause D digits left of the decimal point of the value X to become zero.\n','mysql> SELECT ROUND(-1.23);\n        -> -1\nmysql> SELECT ROUND(-1.58);\n        -> -2\nmysql> SELECT ROUND(1.58);\n        -> 2\nmysql> SELECT ROUND(1.298, 1);\n        -> 1.3\nmysql> SELECT ROUND(1.298, 0);\n        -> 1\nmysql> SELECT ROUND(23.298, -1);\n        -> 20\n','mathematical-functions'),(43,'NULLIF',6,'Syntax:\nNULLIF(expr1,expr2)\n\nReturns NULL if expr1 = expr2 is true, otherwise returns expr1. This is\nthe same as CASE WHEN expr1 = expr2 THEN NULL ELSE expr1 END.\n','mysql> SELECT NULLIF(1,1);\n        -> NULL\nmysql> SELECT NULLIF(1,2);\n        -> 1\n','control-flow-functions'),(44,'CLOSE',35,'Syntax:\nCLOSE cursor_name\n\nThis statement closes a previously opened cursor.\n\nIf not closed explicitly, a cursor is closed at the end of the compound\nstatement in which it was declared.\n','','close'),(45,'STOP SLAVE',25,'Syntax:\nSTOP SLAVE [thread_type [, thread_type] ... ]\n\nthread_type: IO_THREAD | SQL_THREAD\n\nStops the slave threads. STOP SLAVE requires the SUPER privilege.\n\nLike START SLAVE, this statement may be used with the IO_THREAD and\nSQL_THREAD options to name the thread or threads to be stopped.\n','','stop-slave'),(46,'TIMEDIFF',28,'Syntax:\nTIMEDIFF(expr,expr2)\n\nTIMEDIFF() returns the time between the start time expr and the end\ntime expr2. expr and expr2 are time or date-and-time expressions, but\nboth must be of the same type.\n','mysql> SELECT TIMEDIFF(\'2000:01:01 00:00:00\',\n    ->                 \'2000:01:01 00:00:00.000001\');\n        -> \'-00:00:00.000001\'\nmysql> SELECT TIMEDIFF(\'1997-12-31 23:59:59.000001\',\n    ->                 \'1997-12-30 01:01:01.000002\');\n        -> \'46:58:57.999999\'\n','date-and-time-functions'),(47,'LINEFROMTEXT',3,'LineFromText(wkt[,srid]), LineStringFromText(wkt[,srid])\n\nConstructs a LINESTRING value using its WKT representation and SRID.\n','','gis-wkt-functions'),(48,'SHOW MASTER STATUS',25,'Syntax:\nSHOW MASTER STATUS\n\nProvides status information about the binary log files of the master.\nExample:\n\nmysql > SHOW MASTER STATUS;\n+---------------+----------+--------------+------------------+\n| File          | Position | Binlog_Do_DB | Binlog_Ignore_DB |\n+---------------+----------+--------------+------------------+\n| mysql-bin.003 | 73       | test         | manual,mysql     |\n+---------------+----------+--------------+------------------+\n','','show-master-status'),(49,'ADDTIME',28,'Syntax:\nADDTIME(expr,expr2)\n\nADDTIME() adds expr2 to expr and returns the result. expr is a time or\ndatetime expression, and expr2 is a time expression.\n','mysql> SELECT ADDTIME(\'1997-12-31 23:59:59.999999\',\n    ->                \'1 1:1:1.000002\');\n        -> \'1998-01-02 01:01:01.000001\'\nmysql> SELECT ADDTIME(\'01:00:00.999999\', \'02:00:00.999998\');\n        -> \'03:00:01.999997\'\n','date-and-time-functions'),(50,'SPATIAL',30,'MySQL can create spatial indexes using syntax similar to that for\ncreating regular indexes, but extended with the SPATIAL keyword.\nCurrently, spatial columns that are indexed must be declared NOT NULL.\nThe following examples demonstrate how to create spatial indexes:\n\no With CREATE TABLE:\n\nCREATE TABLE geom (g GEOMETRY NOT NULL, SPATIAL INDEX(g));\n\no With ALTER TABLE:\n\nALTER TABLE geom ADD SPATIAL INDEX(g);\n\no With CREATE INDEX:\n\nCREATE SPATIAL INDEX sp_index ON geom (g);\n\nFor MyISAM tables, SPATIAL INDEX creates an R-tree index. For other\nstorage engines that support spatial indexing, SPATIAL INDEX creates a\nB-tree index. A B-tree index on spatial values will be useful for\nexact-value lookups, but not for range scans.\n\nTo drop spatial indexes, use ALTER TABLE or DROP INDEX:\n\no With ALTER TABLE:\n\nALTER TABLE geom DROP INDEX g;\n\no With DROP INDEX:\n\nDROP INDEX sp_index ON geom;\n\nExample: Suppose that a table geom contains more than 32,000\ngeometries, which are stored in the column g of type GEOMETRY. The\ntable also has an AUTO_INCREMENT column fid for storing object ID\nvalues.\n','','creating-spatial-indexes'),(51,'TIMESTAMPDIFF',28,'Syntax:\nTIMESTAMPDIFF(interval,datetime_expr1,datetime_expr2)\n\nReturns the integer difference between the date or datetime expressions\ndatetime_expr1 and datetime_expr2. The unit for the result is given by\nthe interval argument. The legal values for interval are the same as\nthose listed in the description of the TIMESTAMPADD() function.\n','mysql> SELECT TIMESTAMPDIFF(MONTH,\'2003-02-01\',\'2003-05-01\');\n        -> 3\nmysql> SELECT TIMESTAMPDIFF(YEAR,\'2002-05-01\',\'2001-01-01\');\n        -> -1\n','date-and-time-functions'),(52,'UPPER',33,'Syntax:\nUPPER(str)\n\nReturns the string str with all characters changed to uppercase\naccording to the current character set mapping. The default is latin1\n(cp1252 West European).\n','mysql> SELECT UPPER(\'Hej\');\n        -> \'HEJ\'\n','string-functions'),(53,'FROM_UNIXTIME',28,'Syntax:\nFROM_UNIXTIME(unix_timestamp), FROM_UNIXTIME(unix_timestamp,format)\n\nReturns a representation of the unix_timestamp argument as a value in\n\'YYYY-MM-DD HH:MM:SS\' or YYYYMMDDHHMMSS format, depending on whether\nthe function is used in a string or numeric context. unix_timestamp is\nan internal timestamp value such as is produced by the UNIX_TIMESTAMP()\nfunction.\n\nIf format is given, the result is formatted according to the format\nstring, which is used the same way as listed in the entry for the\nDATE_FORMAT() function.\n','mysql> SELECT FROM_UNIXTIME(875996580);\n        -> \'1997-10-04 22:23:00\'\nmysql> SELECT FROM_UNIXTIME(875996580) + 0;\n        -> 19971004222300\nmysql> SELECT FROM_UNIXTIME(UNIX_TIMESTAMP(),\n    ->                      \'%Y %D %M %h:%i:%s %x\');\n        -> \'2003 6th August 06:22:58 2003\'\n','date-and-time-functions'),(54,'MEDIUMBLOB',20,'MEDIUMBLOB\n\nA BLOB column with a maximum length of 16,777,215 (224 - 1) bytes.\n','','string-type-overview'),(55,'IFNULL',6,'Syntax:\nIFNULL(expr1,expr2)\n\nIf expr1 is not NULL, IFNULL() returns expr1; otherwise it returns\nexpr2. IFNULL() returns a numeric or string value, depending on the\ncontext in which it is used.\n','mysql> SELECT IFNULL(1,0);\n        -> 1\nmysql> SELECT IFNULL(NULL,10);\n        -> 10\nmysql> SELECT IFNULL(1/0,10);\n        -> 10\nmysql> SELECT IFNULL(1/0,\'yes\');\n        -> \'yes\'\n','control-flow-functions'),(56,'SHOW ERRORS',25,'Syntax:\nSHOW ERRORS [LIMIT [offset,] row_count]\nSHOW COUNT(*) ERRORS\n\nThis statement is similar to SHOW WARNINGS, except that instead of\ndisplaying errors, warnings, and notes, it displays only errors.\n\nThe LIMIT clause has the same syntax as for the SELECT statement. See\n[select].\n\nThe SHOW COUNT(*) ERRORS statement displays the number of errors. You\ncan also retrieve this number from the error_count variable:\n\nSHOW COUNT(*) ERRORS;\nSELECT @@error_count;\n','','show-errors'),(57,'LEAST',17,'Syntax:\nLEAST(value1,value2,...)\n\nWith two or more arguments, returns the smallest (minimum-valued)\nargument. The arguments are compared using the following rules:\n\no If the return value is used in an INTEGER context or all arguments\n  are integer-valued, they are compared as integers.\n\no If the return value is used in a REAL context or all arguments are\n  real-valued, they are compared as reals.\n\no If any argument is a case-sensitive string, the arguments are\n  compared as case-sensitive strings.\n\no In all other cases, the arguments are compared as case-insensitive\n  strings.\n\nBefore MySQL 5.0.13, LEAST() returns NULL only if all arguments are\nNULL. As of 5.0.13, it returns NULL if any argument is NULL.\n','mysql> SELECT LEAST(2,0);\n        -> 0\nmysql> SELECT LEAST(34.0,3.0,5.0,767.0);\n        -> 3.0\nmysql> SELECT LEAST(\'B\',\'A\',\'C\');\n        -> \'A\'\n','comparison-operators'),(58,'=',17,'=\n\nEqual:\n','mysql> SELECT 1 = 0;\n        -> 0\nmysql> SELECT \'0\' = 0;\n        -> 1\nmysql> SELECT \'0.0\' = 0;\n        -> 1\nmysql> SELECT \'0.01\' = 0;\n        -> 0\nmysql> SELECT \'.01\' = 0.01;\n        -> 1\n','comparison-operators'),(59,'REVERSE',33,'Syntax:\nREVERSE(str)\n\nReturns the string str with the order of the characters reversed.\n','mysql> SELECT REVERSE(\'abc\');\n        -> \'cba\'\n','string-functions'),(60,'ISNULL',17,'Syntax:\nISNULL(expr)\n\nIf expr is NULL, ISNULL() returns 1, otherwise it returns 0.\n','mysql> SELECT ISNULL(1+1);\n        -> 0\nmysql> SELECT ISNULL(1/0);\n        -> 1\n','comparison-operators'),(61,'BINARY',20,'BINARY(M)\n\nThe BINARY type is similar to the CHAR type, but stores binary byte\nstrings rather than non-binary character strings.\n','','string-type-overview'),(62,'BLOB DATA TYPE',20,'A BLOB is a binary large object that can hold a variable amount of\ndata. The four BLOB types are TINYBLOB, BLOB, MEDIUMBLOB, and LONGBLOB.\nThese differ only in the maximum length of the values they can hold.\nThe four TEXT types are TINYTEXT, TEXT, MEDIUMTEXT, and LONGTEXT. These\ncorrespond to the four BLOB types and have the same maximum lengths and\nstorage requirements. See [storage-requirements]. No lettercase\nconversion for TEXT or BLOB columns takes place during storage or\nretrieval.\n','','blob'),(63,'BOUNDARY',32,'Boundary(g)\n\nReturns a geometry that is the closure of the combinatorial boundary of\nthe geometry value g.\n','','general-geometry-property-functions'),(64,'CREATE USER',8,'Syntax:\nCREATE USER user [IDENTIFIED BY [PASSWORD] \'password\']\n    [, user [IDENTIFIED BY [PASSWORD] \'password\']] ...\n\nThe CREATE USER statement was added in MySQL 5.0.2. This statement\ncreates new MySQL accounts. To use it, you must have the global CREATE\nUSER privilege or the INSERT privilege for the mysql database. For each\naccount, CREATE USER creates a new record in the mysql.user table that\nhas no privileges. An error occurs if the account already exists. Each\naccount is named using the same format as for the GRANT statement; for\nexample, \'jeffrey\'@\'localhost\'. The user and host parts of the account\nname correspond to the User and Host column values of the user table\nrow for the account.\n\nThe account can be given a password with the optional IDENTIFIED BY\nclause. The user value and the password are given the same way as for\nthe GRANT statement. In particular, to specify the password in plain\ntext, omit the PASSWORD keyword. To specify the password as the hashed\nvalue as returned by the PASSWORD() function, include the PASSWORD\nkeyword. See [grant].\n','','create-user'),(65,'POINT',22,'Point(x,y)\n\nConstructs a WKB Point using its coordinates.\n','','gis-mysql-specific-functions'),(66,'CURRENT_USER',15,'Syntax:\nCURRENT_USER, CURRENT_USER()\n\nReturns the username and hostname combination for the MySQL account\nthat the server used to authenticate the current client. This account\ndetermines your access privileges. As of MySQL 5.0.10, within a stored\nroutine that is defined with the SQL SECURITY DEFINER characteristic,\nCURRENT_USER() returns the creator of the routine. The return value is\na string in the utf8 character set.\n\nThe value of CURRENT_USER() can differ from the value of USER().\n','mysql> SELECT USER();\n        -> \'davida@localhost\'\nmysql> SELECT * FROM mysql.user;\nERROR 1044: Access denied for user \'\'@\'localhost\' to\ndatabase \'mysql\'\nmysql> SELECT CURRENT_USER();\n        -> \'@localhost\'\n','information-functions'),(67,'LCASE',33,'Syntax:\nLCASE(str)\n\nLCASE() is a synonym for LOWER().\n','','string-functions'),(68,'<=',17,'Syntax:\n<=\n\nLess than or equal:\n','mysql> SELECT 0.1 <= 2;\n        -> 1\n','comparison-operators'),(69,'UPDATE',25,'Syntax:\nSingle-table syntax:\n\nUPDATE [LOW_PRIORITY] [IGNORE] tbl_name\n    SET col_name1=expr1 [, col_name2=expr2 ...]\n    [WHERE where_condition]\n    [ORDER BY ...]\n    [LIMIT row_count]\n\nMultiple-table syntax:\n\nUPDATE [LOW_PRIORITY] [IGNORE] table_references\n    SET col_name1=expr1 [, col_name2=expr2 ...]\n    [WHERE where_condition]\n\nFor the single-table syntax, the UPDATE statement updates columns of\nexisting rows in tbl_name with new values. The SET clause indicates\nwhich columns to modify and the values they should be given. The WHERE\nclause, if given, specifies the conditions that identify which rows to\nupdate. With no WHERE clause, all rows are updated. If the ORDER BY\nclause is specified, the rows are updated in the order that is\nspecified. The LIMIT clause places a limit on the number of rows that\ncan be updated.\n\nFor the multiple-table syntax, UPDATE updates rows in each table named\nin table_references that satisfy the conditions. In this case, ORDER BY\nand LIMIT cannot be used.\n\nwhere_condition is an expression that evaluates to true for each row to\nbe updated. It is specified as described in [select].\n\nThe UPDATE statement supports the following modifiers:\n\no If you use the LOW_PRIORITY keyword, execution of the UPDATE is\n  delayed until no other clients are reading from the table.\n\no If you use the IGNORE keyword, the update statement does not abort\n  even if errors occur during the update. Rows for which duplicate-key\n  conflicts occur are not updated. Rows for which columns are updated\n  to values that would cause data conversion errors are updated to the\n  closet valid values instead.\n','','update'),(70,'CASE STATEMENT',35,'Syntax:\nCASE case_value\n    WHEN when_value THEN statement_list\n    [WHEN when_value THEN statement_list] ...\n    [ELSE statement_list]\nEND CASE\n\nOr:\n\nCASE\n    WHEN search_condition THEN statement_list\n    [WHEN search_condition THEN statement_list] ...\n    [ELSE statement_list]\nEND CASE\n\nThe CASE statement for stored routines implements a complex conditional\nconstruct. If a search_condition evaluates to true, the corresponding\nSQL statement list is executed. If no search condition matches, the\nstatement list in the ELSE clause is executed. Each statement_list\nconsists of one or more statements.\n\nNote: The syntax of the CASE statement shown here for use inside stored\nroutines differs slightly from that of the SQL CASE expression\ndescribed in [control-flow-functions]. The CASE statement cannot have\nan ELSE NULL clause, and it is terminated with END CASE instead of END.\n','','case-statement'),(71,'EXECUTE STATEMENT',25,'Syntax:\nEXECUTE stmt_name [USING @var_name [, @var_name] ...]\n\nAfter preparing a statement, you execute it with an EXECUTE statement\nthat refers to the prepared statement name. If the prepared statement\ncontains any parameter markers, you must supply a USING clause that\nlists user variables containing the values to be bound to the\nparameters. Parameter values can be supplied only by user variables,\nand the USING clause must name exactly as many variables as the number\nof parameter markers in the statement.\n\nYou can execute a given prepared statement multiple times, passing\ndifferent variables to it or setting the variables to different values\nbefore each execution.\n','','sqlps'),(72,'DROP INDEX',36,'Syntax:\nDROP INDEX index_name ON tbl_name\n\nDROP INDEX drops the index named index_name from the table tbl_name.\nThis statement is mapped to an ALTER TABLE statement to drop the index.\nSee [alter-table].\n','','drop-index'),(73,'MATCH AGAINST',33,'Syntax:\nMATCH (col1,col2,...) AGAINST (expr [search_modifier])\n\nsearch_modifier: { IN BOOLEAN MODE | WITH QUERY EXPANSION }\n\nMySQL has support for full-text indexing and searching:\n\no A full-text index in MySQL is an index of type FULLTEXT.\n\no Full-text indexes can be used only with MyISAM tables, and can be\n  created only for CHAR, VARCHAR, or TEXT columns.\n\no A FULLTEXT index definition can be given in the CREATE TABLE\n  statement when a table is created, or added later using ALTER TABLE\n  or CREATE INDEX.\n\no For large datasets, it is much faster to load your data into a table\n  that has no FULLTEXT index and then create the index after that, than\n  to load data into a table that has an existing FULLTEXT index.\n\nFull-text searching is performed using MATCH() ... AGAINST syntax.\nMATCH() takes a comma-separated list that names the columns to be\nsearched. AGAINST takes a string to search for, and an optional\nmodifier that indicates what type of search to perform. The search\nstring must be a literal string, not a variable or a column name. There\nare three types of full-text searches:\n\no A boolean search interprets the search string using the rules of a\n  special query language. The string contains the words to search for.\n  It can also contain operators that specify requirements such that a\n  word must be present or absent in matching rows, or that it should be\n  weighted higher or lower than usual. Common words such as \"some\" or\n  \"then\" are stopwords and do not match if present in the search\n  string. The IN BOOLEAN MODE modifier specifies a boolean search. For\n  more information, see [fulltext-boolean].\n\no A natural language search interprets the search string as a phrase in\n  natural human language (a phrase in free text). There are no special\n  operators. The stopword list applies. In addition, words that are\n  present in more than 50% of the rows are considered common and do not\n  match. Full-text searches are natural language searches if no\n  modifier is given.\n\no A query expansion search is a modification of a natural language\n  search. The search string is used to perform a natural language\n  search. Then words from the most relevant rows returned by the search\n  are added to the search string and the search is done again. The\n  query returns the rows from the second search. The WITH QUERY\n  EXPANSION modifier specifies a query expansion search. For more\n  information, see [fulltext-query-expansion].\n','mysql> SELECT id, body, MATCH (title,body) AGAINST\n    -> (\'Security implications of running MySQL as root\') AS score\n    -> FROM articles WHERE MATCH (title,body) AGAINST\n    -> (\'Security implications of running MySQL as root\');\n+----+-------------------------------------+-----------------+\n| id | body                                | score           |\n+----+-------------------------------------+-----------------+\n|  4 | 1. Never run mysqld as root. 2. ... | 1.5219271183014 |\n|  6 | When configured properly, MySQL ... | 1.3114095926285 |\n+----+-------------------------------------+-----------------+\n2 rows in set (0.00 sec)\n','fulltext-search'),(74,'ABS',4,'Syntax:\nABS(X)\n\nReturns the absolute value of X.\n','mysql> SELECT ABS(2);\n        -> 2\nmysql> SELECT ABS(-32);\n        -> 32\n','mathematical-functions'),(75,'POLYFROMWKB',29,'PolyFromWKB(wkb[,srid]), PolygonFromWKB(wkb[,srid])\n\nConstructs a POLYGON value using its WKB representation and SRID.\n','','gis-wkb-functions'),(76,'NOT LIKE',33,'Syntax:\nexpr NOT LIKE pat [ESCAPE \'escape_char\']\n\nThis is the same as NOT (expr LIKE pat [ESCAPE \'escape_char\']).\n','','string-comparison-functions'),(77,'SPACE',33,'Syntax:\nSPACE(N)\n\nReturns a string consisting of N space characters.\n','mysql> SELECT SPACE(6);\n        -> \'      \'\n','string-functions'),(78,'MBR DEFINITION',5,'Its MBR (Minimum Bounding Rectangle), or Envelope. This is the bounding\ngeometry, formed by the minimum and maximum (X,Y) coordinates:\n','((MINX MINY, MAXX MINY, MAXX MAXY, MINX MAXY, MINX MINY))\n','gis-class-geometry'),(79,'GEOMETRYCOLLECTION',22,'GeometryCollection(g1,g2,...)\n\nConstructs a WKB GeometryCollection. If any argument is not a\nwell-formed WKB representation of a geometry, the return value is NULL.\n','','gis-mysql-specific-functions'),(80,'*',4,'Syntax:\n*\n\nMultiplication:\n','mysql> SELECT 3*5;\n        -> 15\nmysql> SELECT 18014398509481984*18014398509481984.0;\n        -> 324518553658426726783156020576256.0\nmysql> SELECT 18014398509481984*18014398509481984;\n        -> 0\n','arithmetic-functions'),(81,'TIMESTAMP',20,'TIMESTAMP[(M)]\n\nA timestamp. The range is \'1970-01-01 00:00:00\' to partway through the\nyear 2037.\n\nA TIMESTAMP column is useful for recording the date and time of an\nINSERT or UPDATE operation. By default, the first TIMESTAMP column in a\ntable is automatically set to the date and time of the most recent\noperation if you do not assign it a value yourself. You can also set\nany TIMESTAMP column to the current date and time by assigning it a\nNULL value. Variations on automatic initialization and update\nproperties are described in [timestamp-4-1].\n\nA TIMESTAMP value is returned as a string in the format \'YYYY-MM-DD\nHH:MM:SS\' with a display width fixed at 19 characters. To obtain the\nvalue as a number, you should add +0 to the timestamp column.\n\nNote: The TIMESTAMP format that was used prior to MySQL 4.1 is not\nsupported in MySQL 5.0; see MySQL 3.23, 4.0, 4.1 Reference Manual for\ninformation regarding the old format.\n','','date-and-time-type-overview'),(82,'DES_DECRYPT',10,'Syntax:\nDES_DECRYPT(crypt_str[,key_str])\n\nDecrypts a string encrypted with DES_ENCRYPT(). If an error occurs,\nthis function returns NULL.\n\nNote that this function works only if MySQL has been configured with\nSSL support. See [secure-connections].\n\nIf no key_str argument is given, DES_DECRYPT() examines the first byte\nof the encrypted string to determine the DES key number that was used\nto encrypt the original string, and then reads the key from the DES key\nfile to decrypt the message. For this to work, the user must have the\nSUPER privilege. The key file can be specified with the --des-key-file\nserver option.\n\nIf you pass this function a key_str argument, that string is used as\nthe key for decrypting the message.\n\nIf the crypt_str argument does not appear to be an encrypted string,\nMySQL returns the given crypt_str.\n','','encryption-functions'),(83,'ENDPOINT',11,'EndPoint(ls)\n\nReturns the Point that is the endpoint of the LineString value ls.\n','mysql> SET @ls = \'LineString(1 1,2 2,3 3)\';\nmysql> SELECT AsText(EndPoint(GeomFromText(@ls)));\n+-------------------------------------+\n| AsText(EndPoint(GeomFromText(@ls))) |\n+-------------------------------------+\n| POINT(3 3)                          |\n+-------------------------------------+\n','linestring-property-functions'),(84,'CACHE INDEX',25,'Syntax:\nCACHE INDEX\n  tbl_index_list [, tbl_index_list] ...\n  IN key_cache_name\n\ntbl_index_list:\n  tbl_name [[INDEX|KEY] (index_name[, index_name] ...)]\n\nThe CACHE INDEX statement assigns table indexes to a specific key\ncache. It is used only for MyISAM tables.\n\nThe following statement assigns indexes from the tables t1, t2, and t3\nto the key cache named hot_cache:\n\nmysql> CACHE INDEX t1, t2, t3 IN hot_cache;\n+---------+--------------------+----------+----------+\n| Table   | Op                 | Msg_type | Msg_text |\n+---------+--------------------+----------+----------+\n| test.t1 | assign_to_keycache | status   | OK       |\n| test.t2 | assign_to_keycache | status   | OK       |\n| test.t3 | assign_to_keycache | status   | OK       |\n+---------+--------------------+----------+----------+\n','','cache-index'),(85,'COMPRESS',10,'Syntax:\nCOMPRESS(string_to_compress)\n\nCompresses a string and returns the result as a binary string. This\nfunction requires MySQL to have been compiled with a compression\nlibrary such as zlib. Otherwise, the return value is always NULL. The\ncompressed string can be uncompressed with UNCOMPRESS().\n','mysql> SELECT LENGTH(COMPRESS(REPEAT(\'a\',1000)));\n        -> 21\nmysql> SELECT LENGTH(COMPRESS(\'\'));\n        -> 0\nmysql> SELECT LENGTH(COMPRESS(\'a\'));\n        -> 13\nmysql> SELECT LENGTH(COMPRESS(REPEAT(\'a\',16)));\n        -> 15\n','encryption-functions'),(86,'INSERT',25,'Syntax:\nINSERT [LOW_PRIORITY | DELAYED | HIGH_PRIORITY] [IGNORE]\n    [INTO] tbl_name [(col_name,...)]\n    VALUES ({expr | DEFAULT},...),(...),...\n    [ ON DUPLICATE KEY UPDATE col_name=expr, ... ]\n\nOr:\n\nINSERT [LOW_PRIORITY | DELAYED | HIGH_PRIORITY] [IGNORE]\n    [INTO] tbl_name\n    SET col_name={expr | DEFAULT}, ...\n    [ ON DUPLICATE KEY UPDATE col_name=expr, ... ]\n\nOr:\n\nINSERT [LOW_PRIORITY | HIGH_PRIORITY] [IGNORE]\n    [INTO] tbl_name [(col_name,...)]\n    SELECT ...\n    [ ON DUPLICATE KEY UPDATE col_name=expr, ... ]\n\nINSERT inserts new rows into an existing table. The INSERT ... VALUES\nand INSERT ... SET forms of the statement insert rows based on\nexplicitly specified values. The INSERT ... SELECT form inserts rows\nselected from another table or tables. INSERT ... SELECT is discussed\nfurther in [insert-select].\n','','insert'),(87,'COUNT',14,'Syntax:\nCOUNT(expr)\n\nReturns a count of the number of non-NULL values in the rows retrieved\nby a SELECT statement.\n\nCOUNT() returns 0 if there were no matching rows.\n','mysql> SELECT student.student_name,COUNT(*)\n    ->        FROM student,course\n    ->        WHERE student.student_id=course.student_id\n    ->        GROUP BY student_name;\n','group-by-functions'),(88,'HANDLER',25,'Syntax:\nHANDLER tbl_name OPEN [ AS alias ]\nHANDLER tbl_name READ index_name { = | >= | <= | < } (value1,value2,...)\n    [ WHERE where_condition ] [LIMIT ... ]\nHANDLER tbl_name READ index_name { FIRST | NEXT | PREV | LAST }\n    [ WHERE where_condition ] [LIMIT ... ]\nHANDLER tbl_name READ { FIRST | NEXT }\n    [ WHERE where_condition ] [LIMIT ... ]\nHANDLER tbl_name CLOSE\n\nThe HANDLER statement provides direct access to table storage engine\ninterfaces. It is available for MyISAM and InnoDB tables.\n','','handler'),(89,'MLINEFROMTEXT',3,'MLineFromText(wkt[,srid]), MultiLineStringFromText(wkt[,srid])\n\nConstructs a MULTILINESTRING value using its WKT representation and\nSRID.\n','','gis-wkt-functions'),(90,'GEOMCOLLFROMWKB',29,'GeomCollFromWKB(wkb[,srid]), GeometryCollectionFromWKB(wkb[,srid])\n\nConstructs a GEOMETRYCOLLECTION value using its WKB representation and\nSRID.\n','','gis-wkb-functions'),(91,'RENAME TABLE',36,'Syntax:\nRENAME TABLE tbl_name TO new_tbl_name\n    [, tbl_name2 TO new_tbl_name2] ...\n\nThis statement renames one or more tables.\n\nThe rename operation is done atomically, which means that no other\nthread can access any of the tables while the rename is running. For\nexample, if you have an existing table old_table, you can create\nanother table new_table that has the same structure but is empty, and\nthen replace the existing table with the empty one as follows (assuming\nthat backup_table does not already exist):\n','CREATE TABLE new_table (...);\nRENAME TABLE old_table TO backup_table, new_table TO old_table;\n','rename-table'),(92,'BOOLEAN',20,'BOOL, BOOLEAN\n\nThese types are synonyms for TINYINT(1). A value of zero is considered\nfalse. Non-zero values are considered true.\n\nIn the future, full boolean type handling will be introduced in\naccordance with standard SQL.\n','','numeric-type-overview'),(93,'DEFAULT',13,'Syntax:\nDEFAULT(col_name)\n\nReturns the default value for a table column. Starting with MySQL\n5.0.2, an error results if the column has no default value.\n','mysql> UPDATE t SET i = DEFAULT(i)+1 WHERE id < 100;\n','miscellaneous-functions'),(94,'TINYTEXT',20,'TINYTEXT\n\nA TEXT column with a maximum length of 255 (28 - 1) characters.\n','','string-type-overview'),(95,'OPTIMIZE TABLE',19,'Syntax:\nOPTIMIZE [LOCAL | NO_WRITE_TO_BINLOG] TABLE tbl_name [, tbl_name] ...\n\nOPTIMIZE TABLE should be used if you have deleted a large part of a\ntable or if you have made many changes to a table with variable-length\nrows (tables that have VARCHAR, VARBINARY, BLOB, or TEXT columns).\nDeleted rows are maintained in a linked list and subsequent INSERT\noperations reuse old row positions. You can use OPTIMIZE TABLE to\nreclaim the unused space and to defragment the data file.\n','','optimize-table'),(96,'DECODE',10,'Syntax:\nDECODE(crypt_str,pass_str)\n\nDecrypts the encrypted string crypt_str using pass_str as the password.\ncrypt_str should be a string returned from ENCODE().\n','','encryption-functions'),(97,'<=>',17,'Syntax:\n<=>\n\nNULL-safe equal. This operator performs an equality comparison like the\n= operator, but returns 1 rather than NULL if both operands are NULL,\nand 0 rather than NULL if one operand is NULL.\n','mysql> SELECT 1 <=> 1, NULL <=> NULL, 1 <=> NULL;\n        -> 1, 1, 0\nmysql> SELECT 1 = 1, NULL = NULL, 1 = NULL;\n        -> 1, NULL, NULL\n','comparison-operators'),(98,'LOAD DATA FROM MASTER',25,'Syntax:\nLOAD DATA FROM MASTER\n\nThis statement takes a snapshot of the master and copies it to the\nslave. It updates the values of MASTER_LOG_FILE and MASTER_LOG_POS so\nthat the slave starts replicating from the correct position. Any table\nand database exclusion rules specified with the --replicate-*-do-* and\n--replicate-*-ignore-* options are honored. --replicate-rewrite-db is\nnot taken into account because a user could use this option to set up a\nnon-unique mapping such as --replicate-rewrite-db=\"db1->db3\" and\n--replicate-rewrite-db=\"db2->db3\", which would confuse the slave when\nloading tables from the master.\n\nUse of this statement is subject to the following conditions:\n\no It works only for MyISAM tables. Attempting to load a non-MyISAM\n  table results in the following error:\n\nERROR 1189 (08S01): Net error reading from master\n\no It acquires a global read lock on the master while taking the\n  snapshot, which prevents updates on the master during the load\n  operation.\n\nIf you are loading large tables, you might have to increase the values\nof net_read_timeout and net_write_timeout on both the master and slave\nservers. See [server-system-variables].\n\nNote that LOAD DATA FROM MASTER does not copy any tables from the mysql\ndatabase. This makes it easy to have different users and privileges on\nthe master and the slave.\n\nTo use LOAD DATA FROM MASTER, the replication account that is used to\nconnect to the master must have the RELOAD and SUPER privileges on the\nmaster and the SELECT privilege for all master tables you want to load.\nAll master tables for which the user does not have the SELECT privilege\nare ignored by LOAD DATA FROM MASTER. This is because the master hides\nthem from the user: LOAD DATA FROM MASTER calls SHOW DATABASES to know\nthe master databases to load, but SHOW DATABASES returns only databases\nfor which the user has some privilege. See [show-databases]. On the\nslave side, the user that issues LOAD DATA FROM MASTER must have\nprivileges for dropping and creating the databases and tables that are\ncopied.\n','','load-data-from-master'),(99,'RESET',25,'Syntax:\nRESET reset_option [, reset_option] ...\n\nThe RESET statement is used to clear the state of various server\noperations. You must have the RELOAD privilege to execute RESET.\n\nRESET acts as a stronger version of the FLUSH statement. See [flush].\n','','reset'),(100,'GET_LOCK',13,'Syntax:\nGET_LOCK(str,timeout)\n\nTries to obtain a lock with a name given by the string str, using a\ntimeout of timeout seconds. Returns 1 if the lock was obtained\nsuccessfully, 0 if the attempt timed out (for example, because another\nclient has previously locked the name), or NULL if an error occurred\n(such as running out of memory or the thread was killed with mysqladmin\nkill). If you have a lock obtained with GET_LOCK(), it is released when\nyou execute RELEASE_LOCK(), execute a new GET_LOCK(), or your\nconnection terminates (either normally or abnormally).\n\nThis function can be used to implement application locks or to simulate\nrecord locks. Names are locked on a server-wide basis. If a name has\nbeen locked by one client, GET_LOCK() blocks any request by another\nclient for a lock with the same name. This allows clients that agree on\na given lock name to use the name to perform cooperative advisory\nlocking. But be aware that it also allows a client that is not among\nthe set of cooperating clients to lock a name, either inadvertently or\ndeliberately, and thus prevent any of the cooperating clients from\nlocking that name. One way to reduce the likelihood of this is to use\nlock names that are database-specific or application-specific. For\nexample, use lock names of the form db_name.str or app_name.str.\n','mysql> SELECT GET_LOCK(\'lock1\',10);\n        -> 1\nmysql> SELECT IS_FREE_LOCK(\'lock2\');\n        -> 1\nmysql> SELECT GET_LOCK(\'lock2\',10);\n        -> 1\nmysql> SELECT RELEASE_LOCK(\'lock2\');\n        -> 1\nmysql> SELECT RELEASE_LOCK(\'lock1\');\n        -> NULL\n','miscellaneous-functions'),(101,'UCASE',33,'Syntax:\nUCASE(str)\n\nUCASE() is a synonym for UPPER().\n','','string-functions'),(102,'SHOW BINLOG EVENTS',25,'Syntax:\nSHOW BINLOG EVENTS\n   [IN \'log_name\'] [FROM pos] [LIMIT [offset,] row_count]\n\nShows the events in the binary log. If you do not specify \'log_name\',\nthe first binary log is displayed.\n','','show-binlog-events'),(103,'MPOLYFROMWKB',29,'MPolyFromWKB(wkb[,srid]), MultiPolygonFromWKB(wkb[,srid])\n\nConstructs a MULTIPOLYGON value using its WKB representation and SRID.\n','','gis-wkb-functions'),(104,'ITERATE',35,'Syntax:\nITERATE label\n\nITERATE can appear only within LOOP, REPEAT, and WHILE statements.\nITERATE means \"do the loop again.\"\n','CREATE PROCEDURE doiterate(p1 INT)\nBEGIN\n  label1: LOOP\n    SET p1 = p1 + 1;\n    IF p1 < 10 THEN ITERATE label1; END IF;\n    LEAVE label1;\n  END LOOP label1;\n  SET @x = p1;\nEND\n','iterate-statement'),(105,'DO',25,'Syntax:\nDO expr [, expr] ...\n\nDO executes the expressions but does not return any results. In most\nrespects, DO is shorthand for SELECT expr, ..., but has the advantage\nthat it is slightly faster when you do not care about the result.\nHowever, DO does not report any errors. Instead, it reports errors as\nwarnings.\n\nDO is useful primarily with functions that have side effects, such as\nRELEASE_LOCK().\n','','do'),(106,'CURTIME',28,'Syntax:\nCURTIME()\n\nReturns the current time as a value in \'HH:MM:SS\' or HHMMSS format,\ndepending on whether the function is used in a string or numeric\ncontext.\n','mysql> SELECT CURTIME();\n        -> \'23:50:26\'\nmysql> SELECT CURTIME() + 0;\n        -> 235026\n','date-and-time-functions'),(107,'CHAR_LENGTH',33,'Syntax:\nCHAR_LENGTH(str)\n\nReturns the length of the string str, measured in characters. A\nmulti-byte character counts as a single character. This means that for\na string containing five two-byte characters, LENGTH() returns 10,\nwhereas CHAR_LENGTH() returns 5.\n','','string-functions'),(108,'BIGINT',20,'BIGINT[(M)] [UNSIGNED] [ZEROFILL]\n\nA large integer. The signed range is -9223372036854775808 to\n9223372036854775807. The unsigned range is 0 to 18446744073709551615.\n','','numeric-type-overview'),(109,'SET',25,'Syntax:\nSET variable_assignment [, variable_assignment] ...\n\nvariable_assignment:\n      user_var_name = expr\n    | [GLOBAL | SESSION] system_var_name = expr\n    | [@@global. | @@session. | @@]system_var_name = expr\n\nThe SET statement assigns values to different types of variables that\naffect the operation of the server or your client. Older versions of\nMySQL employed SET OPTION, but this syntax is deprecated in favor of\nSET without OPTION.\n','','set-option'),(110,'DATE',20,'DATE\n\nA date. The supported range is \'1000-01-01\' to \'9999-12-31\'. MySQL\ndisplays DATE values in \'YYYY-MM-DD\' format, but allows you to assign\nvalues to DATE columns using either strings or numbers.\n','','date-and-time-type-overview'),(111,'CONV',33,'Syntax:\nCONV(N,from_base,to_base)\n\nConverts numbers between different number bases. Returns a string\nrepresentation of the number N, converted from base from_base to base\nto_base. Returns NULL if any argument is NULL. The argument N is\ninterpreted as an integer, but may be specified as an integer or a\nstring. The minimum base is 2 and the maximum base is 36. If to_base is\na negative number, N is regarded as a signed number. Otherwise, N is\ntreated as unsigned. CONV() works with 64-bit precision.\n','mysql> SELECT CONV(\'a\',16,2);\n        -> \'1010\'\nmysql> SELECT CONV(\'6E\',18,8);\n        -> \'172\'\nmysql> SELECT CONV(-17,10,-18);\n        -> \'-H\'\nmysql> SELECT CONV(10+\'10\'+\'10\'+0xa,10,10);\n        -> \'40\'\n','string-functions'),(112,'SHOW OPEN TABLES',25,'Syntax:\nSHOW OPEN TABLES [FROM db_name] [LIKE \'pattern\']\n\nSHOW OPEN TABLES lists the non-TEMPORARY tables that are currently open\nin the table cache. See [table-cache].\n','','show-open-tables'),(113,'EXTRACT',28,'Syntax:\nEXTRACT(type FROM date)\n\nThe EXTRACT() function uses the same kinds of interval type specifiers\nas DATE_ADD() or DATE_SUB(), but extracts parts from the date rather\nthan performing date arithmetic.\n','mysql> SELECT EXTRACT(YEAR FROM \'1999-07-02\');\n       -> 1999\nmysql> SELECT EXTRACT(YEAR_MONTH FROM \'1999-07-02 01:02:03\');\n       -> 199907\nmysql> SELECT EXTRACT(DAY_MINUTE FROM \'1999-07-02 01:02:03\');\n       -> 20102\nmysql> SELECT EXTRACT(MICROSECOND\n    ->                FROM \'2003-01-02 10:30:00.00123\');\n        -> 123\n','date-and-time-functions'),(114,'ENCRYPT',10,'Syntax:\nENCRYPT(str[,salt])\n\nEncrypts str using the Unix crypt() system call and returns a binary\nstring. The salt argument should be a string with at least two\ncharacters. If no salt argument is given, a random value is used.\n','mysql> SELECT ENCRYPT(\'hello\');\n        -> \'VxuFAJXVARROc\'\n','encryption-functions'),(115,'SHOW STATUS',25,'Syntax:\nSHOW [GLOBAL | SESSION] STATUS [LIKE \'pattern\']\n\nSHOW STATUS provides server status information. This information also\ncan be obtained using the mysqladmin extended-status command.\nWith a LIKE clause, the statement displays only those variables that\nmatch the pattern:\n\nmysql> SHOW STATUS LIKE \'Key%\';\n+--------------------+----------+\n| Variable_name      | Value    |\n+--------------------+----------+\n| Key_blocks_used    | 14955    |\n| Key_read_requests  | 96854827 |\n| Key_reads          | 162040   |\n| Key_write_requests | 7589728  |\n| Key_writes         | 3813196  |\n+--------------------+----------+\n\nThe GLOBAL and SESSION options are new in MySQL 5.0.2. With the GLOBAL\nmodifier, SHOW STATUS displays the status values for all connections to\nMySQL. With SESSION, it displays the status values for the current\nconnection. If no modifier is present, the default is SESSION. LOCAL is\na synonym for SESSION.\n\nSome status variables have only a global value. For these, you get the\nsame value for both GLOBAL and SESSION.\n','','show-status'),(116,'OLD_PASSWORD',10,'Syntax:\nOLD_PASSWORD(str)\n\nOLD_PASSWORD() was added to MySQL when the implementation of PASSWORD()\nwas changed to improve security. OLD_PASSWORD() returns the value of\nthe old (pre-4.1) implementation of PASSWORD() as a binary string, and\nis intended to permit you to reset passwords for any pre-4.1 clients\nthat need to connect to your version 5.0 MySQL server without locking\nthem out. See [password-hashing].\n','','encryption-functions'),(117,'SET VARIABLE',35,'Syntax:\nSET var_name = expr [, var_name = expr] ...\n\nThe SET statement in stored routines is an extended version of the\ngeneral SET statement. Referenced variables may be ones declared inside\na routine, or global system variables.\n\nThe SET statement in stored routines is implemented as part of the\npre-existing SET syntax. This allows an extended syntax of SET a=x,\nb=y, ... where different variable types (locally declared variables and\nglobal and session server variables) can be mixed. This also allows\ncombinations of local variables and some options that make sense only\nfor system variables; in that case, the options are recognized but\nignored.\n','','set-statement'),(118,'FORMAT',33,'Syntax:\nFORMAT(X,D)\n\nFormats the number X to a format like \'#,###,###.##\', rounded to D\ndecimal places, and returns the result as a string. If D is 0, the\nresult has no decimal point or fractional part.\n','mysql> SELECT FORMAT(12332.123456, 4);\n        -> \'12,332.1235\'\nmysql> SELECT FORMAT(12332.1,4);\n        -> \'12,332.1000\'\nmysql> SELECT FORMAT(12332.2,0);\n        -> \'12,332\'\n','string-functions'),(119,'||',12,'Syntax:\nOR, ||\n\nLogical OR. When both operands are non-NULL, the result is 1 if any\noperand is non-zero, and 0 otherwise. With a NULL operand, the result\nis 1 if the other operand is non-zero, and NULL otherwise. If both\noperands are NULL, the result is NULL.\n','mysql> SELECT 1 || 1;\n        -> 1\nmysql> SELECT 1 || 0;\n        -> 1\nmysql> SELECT 0 || 0;\n        -> 0\nmysql> SELECT 0 || NULL;\n        -> NULL\nmysql> SELECT 1 || NULL;\n        -> 1\n','logical-operators'),(120,'BIT_LENGTH',33,'Syntax:\nBIT_LENGTH(str)\n\nReturns the length of the string str in bits.\n','mysql> SELECT BIT_LENGTH(\'text\');\n        -> 32\n','string-functions'),(121,'EXTERIORRING',2,'ExteriorRing(poly)\n\nReturns the exterior ring of the Polygon value poly as a LineString.\n','mysql> SET @poly =\n    -> \'Polygon((0 0,0 3,3 3,3 0,0 0),(1 1,1 2,2 2,2 1,1 1))\';\nmysql> SELECT AsText(ExteriorRing(GeomFromText(@poly)));\n+-------------------------------------------+\n| AsText(ExteriorRing(GeomFromText(@poly))) |\n+-------------------------------------------+\n| LINESTRING(0 0,0 3,3 3,3 0,0 0)           |\n+-------------------------------------------+\n','polygon-property-functions'),(122,'GEOMFROMWKB',29,'GeomFromWKB(wkb[,srid]), GeometryFromWKB(wkb[,srid])\n\nConstructs a geometry value of any type using its WKB representation\nand SRID.\n','','gis-wkb-functions'),(123,'SHOW SLAVE HOSTS',25,'Syntax:\nSHOW SLAVE HOSTS\n\nDisplays a list of replication slaves currently registered with the\nmaster. Any slave not started with the --report-host=slave_name option\nis not visible in this list.\n','','show-slave-hosts'),(124,'START TRANSACTION',7,'Syntax:\nSTART TRANSACTION | BEGIN [WORK]\nCOMMIT [WORK] [AND [NO] CHAIN] [[NO] RELEASE]\nROLLBACK [WORK] [AND [NO] CHAIN] [[NO] RELEASE]\nSET AUTOCOMMIT = {0 | 1}\n\nThe START TRANSACTION and BEGIN statement begin a new transaction.\nCOMMIT commits the current transaction, making its changes permanent.\nROLLBACK rolls back the current transaction, canceling its changes. The\nSET AUTOCOMMIT statement disables or enables the default autocommit\nmode for the current connection.\n\nBeginning with MySQL 5.0.3, the optional WORK keyword is supported for\nCOMMIT and RELEASE, as are the CHAIN and RELEASE clauses. CHAIN and\nRELEASE can be used for additional control over transaction completion.\nThe value of the completion_type system variable determines the default\ncompletion behavior. See [server-system-variables].\n\nThe AND CHAIN clause causes a new transaction to begin as soon as the\ncurrent one ends, and the new transaction has the same isolation level\nas the just-terminated transaction. The RELEASE clause causes the\nserver to disconnect the current client connection after terminating\nthe current transaction. Including the NO keyword suppresses CHAIN or\nRELEASE completion, which can be useful if the completion_type system\nvariable is set to cause chaining or release completion by default.\n\nBy default, MySQL runs with autocommit mode enabled. This means that as\nsoon as you execute a statement that updates (modifies) a table, MySQL\nstores the update on disk.\n\nIf you are using a transaction-safe storage engine (such as InnoDB,\nBDB, or NDB Cluster), you can disable autocommit mode with the\nfollowing statement:\n\nSET AUTOCOMMIT=0;\n\nAfter disabling autocommit mode by setting the AUTOCOMMIT variable to\nzero, you must use COMMIT to store your changes to disk or ROLLBACK if\nyou want to ignore the changes you have made since the beginning of\nyour transaction.\n\nTo disable autocommit mode for a single series of statements, use the\nSTART TRANSACTION statement:\n','START TRANSACTION;\nSELECT @A:=SUM(salary) FROM table1 WHERE type=1;\nUPDATE table2 SET summary=@A WHERE type=1;\nCOMMIT;\n','commit'),(125,'BETWEEN AND',17,'Syntax:\nexpr BETWEEN min AND max\n\nIf expr is greater than or equal to min and expr is less than or equal\nto max, BETWEEN returns 1, otherwise it returns 0. This is equivalent\nto the expression (min <= expr AND expr <= max) if all the arguments\nare of the same type. Otherwise type conversion takes place according\nto the rules described in [type-conversion], but applied to all the\nthree arguments.\n','mysql> SELECT 1 BETWEEN 2 AND 3;\n        -> 0\nmysql> SELECT \'b\' BETWEEN \'a\' AND \'c\';\n        -> 1\nmysql> SELECT 2 BETWEEN 2 AND \'3\';\n        -> 1\nmysql> SELECT 2 BETWEEN 2 AND \'x-3\';\n        -> 0\n','comparison-operators'),(126,'MULTIPOLYGON',22,'MultiPolygon(poly1,poly2,...)\n\nConstructs a WKB MultiPolygon value from a set of WKB Polygon\narguments. If any argument is not a WKB Polygon, the return value is\nNULL.\n','','gis-mysql-specific-functions'),(127,'TIME_FORMAT',28,'Syntax:\nTIME_FORMAT(time,format)\n\nThis is used like the DATE_FORMAT() function, but the format string may\ncontain format specifiers only for hours, minutes, and seconds. Other\nspecifiers produce a NULL value or 0.\n','mysql> SELECT TIME_FORMAT(\'100:00:00\', \'%H %k %h %I %l\');\n        -> \'100 100 04 04 4\'\n','date-and-time-functions'),(128,'LEFT',33,'Syntax:\nLEFT(str,len)\n\nReturns the leftmost len characters from the string str.\n','mysql> SELECT LEFT(\'foobarbar\', 5);\n        -> \'fooba\'\n','string-functions'),(129,'FLUSH QUERY CACHE',24,'You can defragment the query cache to better utilize its memory with\nthe FLUSH QUERY CACHE statement. The statement does not remove any\nqueries from the cache.\n\nThe RESET QUERY CACHE statement removes all query results from the\nquery cache. The FLUSH TABLES statement also does this.\n','','query-cache-status-and-maintenance'),(130,'SET DATA TYPE',20,'SET(\'value1\',\'value2\',...)\n\nA set. A string object that can have zero or more values, each of which\nmust be chosen from the list of values \'value1\', \'value2\', ... A SET\ncolumn can have a maximum of 64 members. SET values are represented\ninternally as integers.\n','','string-type-overview'),(131,'RAND',4,'Syntax:\nRAND(), RAND(N)\n\nReturns a random floating-point value v between 0 and 1 inclusive (that\nis, in the range 0 <= v <= 1.0). If an integer argument N is specified,\nit is used as the seed value, which produces a repeatable sequence.\n','mysql> SELECT RAND();\n        -> 0.9233482386203\nmysql> SELECT RAND(20);\n        -> 0.15888261251047\nmysql> SELECT RAND(20);\n        -> 0.15888261251047\nmysql> SELECT RAND();\n        -> 0.63553050033332\nmysql> SELECT RAND();\n        -> 0.70100469486881\nmysql> SELECT RAND(20);\n        -> 0.15888261251047\n','mathematical-functions'),(132,'RPAD',33,'Syntax:\nRPAD(str,len,padstr)\n\nReturns the string str, right-padded with the string padstr to a length\nof len characters. If str is longer than len, the return value is\nshortened to len characters.\n','mysql> SELECT RPAD(\'hi\',5,\'?\');\n        -> \'hi???\'\nmysql> SELECT RPAD(\'hi\',1,\'?\');\n        -> \'h\'\n','string-functions'),(133,'CREATE DATABASE',36,'Syntax:\nCREATE {DATABASE | SCHEMA} [IF NOT EXISTS] db_name\n    [create_specification [, create_specification] ...]\n\ncreate_specification:\n    [DEFAULT] CHARACTER SET charset_name\n  | [DEFAULT] COLLATE collation_name\n\nCREATE DATABASE creates a database with the given name. To use CREATE\nDATABASE, you need the CREATE privilege on the database. CREATE SCHEMA\nis a synonym for CREATE DATABASE as of MySQL 5.0.2.\n','','create-database'),(134,'DEC',20,'DEC[(M[,D])] [UNSIGNED] [ZEROFILL], NUMERIC[(M[,D])] [UNSIGNED]\n[ZEROFILL], FIXED[(M[,D])] [UNSIGNED] [ZEROFILL]\n\nThese types are synonyms for DECIMAL. The FIXED synonym is available\nfor compatibility with other database systems.\n','','numeric-type-overview'),(135,'VAR_POP',14,'Syntax:\nVAR_POP(expr)\n\nReturns the population standard variance of expr. It considers rows as\nthe whole population, not as a sample, so it has the number of rows as\nthe denominator. This function was added in MySQL 5.0.3. Before 5.0.3,\nyou can use VARIANCE(), which is equivalent but is not standard SQL.\n\nVAR_POP() returns NULL if there were no matching rows.\n','','group-by-functions'),(136,'ELT',33,'Syntax:\nELT(N,str1,str2,str3,...)\n\nReturns str1 if N = 1, str2 if N = 2, and so on. Returns NULL if N is\nless than 1 or greater than the number of arguments. ELT() is the\ncomplement of FIELD().\n','mysql> SELECT ELT(1, \'ej\', \'Heja\', \'hej\', \'foo\');\n        -> \'ej\'\nmysql> SELECT ELT(4, \'ej\', \'Heja\', \'hej\', \'foo\');\n        -> \'foo\'\n','string-functions'),(137,'ALTER VIEW',36,'Syntax:\nALTER\n    [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}]\n    [DEFINER = { user | CURRENT_USER }]\n    [SQL SECURITY { DEFINER | INVOKER }]\n    VIEW view_name [(column_list)]\n    AS select_statement\n    [WITH [CASCADED | LOCAL] CHECK OPTION]\n\nThis statement changes the definition of an existing view. The syntax\nis similar to that for CREATE VIEW. See [create-view]. This statement\nrequires the CREATE VIEW and DROP privileges for the view, and some\nprivilege for each column referred to in the SELECT statement.\n','','alter-view'),(138,'SHOW DATABASES',25,'Syntax:\nSHOW {DATABASES | SCHEMAS} [LIKE \'pattern\']\n\nSHOW DATABASES lists the databases on the MySQL server host. SHOW\nSCHEMAS is a synonym for SHOW DATABASES as of MySQL 5.0.2.\n\nYou see only those databases for which you have some kind of privilege,\nunless you have the global SHOW DATABASES privilege. You can also get\nthis list using the mysqlshow command.\n\nIf the server was started with the --skip-show-database option, you\ncannot use this statement at all unless you have the SHOW DATABASES\nprivilege.\n','','show-databases'),(139,'~',18,'Syntax:\n~\n\nInvert all bits.\n','mysql> SELECT 5 & ~1;\n        -> 4\n','bit-functions'),(140,'TEXT',20,'TEXT[(M)]\n\nA TEXT column with a maximum length of 65,535 (216 - 1) characters.\n\nAn optional length M can be given for this type. If this is done, MySQL\ncreates the column as the smallest TEXT type large enough to hold\nvalues M characters long.\n','','string-type-overview'),(141,'CONCAT_WS',33,'Syntax:\nCONCAT_WS(separator,str1,str2,...)\n\nCONCAT_WS() stands for Concatenate With Separator and is a special form\nof CONCAT(). The first argument is the separator for the rest of the\narguments. The separator is added between the strings to be\nconcatenated. The separator can be a string, as can the rest of the\narguments. If the separator is NULL, the result is NULL.\n','mysql> SELECT CONCAT_WS(\',\',\'First name\',\'Second name\',\'Last Name\');\n        -> \'First name,Second name,Last Name\'\nmysql> SELECT CONCAT_WS(\',\',\'First name\',NULL,\'Last Name\');\n        -> \'First name,Last Name\'\n','string-functions'),(142,'ROW_COUNT',15,'Syntax:\nROW_COUNT()\n\nROW_COUNT() returns the number of rows updated, inserted, or deleted by\nthe preceding statement. This is the same as the row count that the\nmysql client displays and the value from the mysql_affected_rows() C\nAPI function.\n','mysql> INSERT INTO t VALUES(1),(2),(3);\nQuery OK, 3 rows affected (0.00 sec)\nRecords: 3  Duplicates: 0  Warnings: 0\n\nmysql> SELECT ROW_COUNT();\n+-------------+\n| ROW_COUNT() |\n+-------------+\n|           3 |\n+-------------+\n1 row in set (0.00 sec)\n\nmysql> DELETE FROM t WHERE i IN(1,2);\nQuery OK, 2 rows affected (0.00 sec)\n\nmysql> SELECT ROW_COUNT();\n+-------------+\n| ROW_COUNT() |\n+-------------+\n|           2 |\n+-------------+\n1 row in set (0.00 sec)\n','information-functions'),(143,'ASIN',4,'Syntax:\nASIN(X)\n\nReturns the arc sine of X, that is, the value whose sine is X. Returns\nNULL if X is not in the range -1 to 1.\n','mysql> SELECT ASIN(0.2);\n        -> 0.20135792079033\nmysql> SELECT ASIN(\'foo\');\n\n+-------------+\n| ASIN(\'foo\') |\n+-------------+\n|           0 |\n+-------------+\n1 row in set, 1 warning (0.00 sec)\n\nmysql> SHOW WARNINGS;\n+---------+------+-----------------------------------------+\n| Level   | Code | Message                                 |\n+---------+------+-----------------------------------------+\n| Warning | 1292 | Truncated incorrect DOUBLE value: \'foo\' |\n+---------+------+-----------------------------------------+\n','mathematical-functions'),(144,'SHOW LOGS',25,'Syntax:\nSHOW [BDB] LOGS\n\nIn MySQL 5.0, this is a deprecated synonym for SHOW ENGINE BDB LOGS.\nSee [show-engine].\n','','show-logs'),(145,'SIGN',4,'Syntax:\nSIGN(X)\n\nReturns the sign of the argument as -1, 0, or 1, depending on whether X\nis negative, zero, or positive.\n','mysql> SELECT SIGN(-32);\n        -> -1\nmysql> SELECT SIGN(0);\n        -> 0\nmysql> SELECT SIGN(234);\n        -> 1\n','mathematical-functions'),(146,'SEC_TO_TIME',28,'Syntax:\nSEC_TO_TIME(seconds)\n\nReturns the seconds argument, converted to hours, minutes, and seconds,\nas a value in \'HH:MM:SS\' or HHMMSS format, depending on whether the\nfunction is used in a string or numeric context.\n','mysql> SELECT SEC_TO_TIME(2378);\n        -> \'00:39:38\'\nmysql> SELECT SEC_TO_TIME(2378) + 0;\n        -> 3938\n','date-and-time-functions'),(147,'FLOAT',20,'FLOAT[(M,D)] [UNSIGNED] [ZEROFILL]\n\nA small (single-precision) floating-point number. Allowable values are\n-3.402823466E+38 to -1.175494351E-38, 0, and 1.175494351E-38 to\n3.402823466E+38. These are the theoretical limits, based on the IEEE\nstandard. The actual range might be slightly smaller depending on your\nhardware or operating system.\n\nM is the total number of decimal digits and D is the number of digits\nfollowing the decimal point. If M and D are omitted, values are stored\nto the limits allowed by the hardware. A single-precision\nfloating-point number is accurate to approximately 7 decimal places.\n\nUNSIGNED, if specified, disallows negative values.\n\nUsing FLOAT might give you some unexpected problems because all\ncalculations in MySQL are done with double precision. See\n[no-matching-rows].\n','','numeric-type-overview'),(148,'LOCATE',33,'Syntax:\nLOCATE(substr,str), LOCATE(substr,str,pos)\n\nThe first syntax returns the position of the first occurrence of\nsubstring substr in string str. The second syntax returns the position\nof the first occurrence of substring substr in string str, starting at\nposition pos. Returns 0 if substr is not in str.\n','mysql> SELECT LOCATE(\'bar\', \'foobarbar\');\n        -> 4\nmysql> SELECT LOCATE(\'xbar\', \'foobar\');\n        -> 0\nmysql> SELECT LOCATE(\'bar\', \'foobarbar\', 5);\n        -> 7\n','string-functions'),(149,'CHARSET',15,'Syntax:\nCHARSET(str)\n\nReturns the character set of the string argument.\n','mysql> SELECT CHARSET(\'abc\');\n        -> \'latin1\'\nmysql> SELECT CHARSET(CONVERT(\'abc\' USING utf8));\n        -> \'utf8\'\nmysql> SELECT CHARSET(USER());\n        -> \'utf8\'\n','information-functions'),(150,'SUBDATE',28,'Syntax:\nSUBDATE(date,INTERVAL expr type), SUBDATE(expr,days)\n\nWhen invoked with the INTERVAL form of the second argument, SUBDATE()\nis a synonym for DATE_SUB(). For information on the INTERVAL argument,\nsee the discussion for DATE_ADD().\n\nmysql> SELECT DATE_SUB(\'1998-01-02\', INTERVAL 31 DAY);\n        -> \'1997-12-02\'\nmysql> SELECT SUBDATE(\'1998-01-02\', INTERVAL 31 DAY);\n        -> \'1997-12-02\'\n\nThe second form allows the use of an integer value for days. In such\ncases, it is interpreted as the number of days to be subtracted from\nthe date or datetime expression expr.\n\nmysql> SELECT SUBDATE(\'1998-01-02 12:00:00\', 31);\n        -> \'1997-12-02 12:00:00\'\n\nNote: You cannot use format \"%X%V\" to convert a year-week string to a\ndate because the combination of a year and week does not uniquely\nidentify a year and month if the week crosses a month boundary. To\nconvert a year-week to a date, then you should also specify the\nweekday:\n\nmysql> SELECT STR_TO_DATE(\'200442 Monday\', \'%X%V %W\');\n        -> \'2004-10-18\'\n','','date-and-time-functions'),(151,'DAYOFYEAR',28,'Syntax:\nDAYOFYEAR(date)\n\nReturns the day of the year for date, in the range 1 to 366.\n','mysql> SELECT DAYOFYEAR(\'1998-02-03\');\n        -> 34\n','date-and-time-functions'),(152,'%',4,'Syntax:\nMOD(N,M), N % M, N MOD M\n\nModulo operation. Returns the remainder of N divided by M.\n','mysql> SELECT MOD(234, 10);\n        -> 4\nmysql> SELECT 253 % 7;\n        -> 1\nmysql> SELECT MOD(29,9);\n        -> 2\nmysql> SELECT 29 MOD 9;\n        -> 2\n','mathematical-functions'),(153,'LONGTEXT',20,'LONGTEXT\n\nA TEXT column with a maximum length of 4,294,967,295 or 4GB (232 - 1)\ncharacters. The maximum effective (permitted) length of LONGTEXT\ncolumns depends on the configured maximum packet size in the\nclient/server protocol and available memory.\n','','string-type-overview'),(154,'DISJOINT',26,'Disjoint(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 is spatially disjoint from (does\nnot intersect) g2.\n','','functions-that-test-spatial-relationships-between-geometries'),(155,'KILL',25,'Syntax:\nKILL [CONNECTION | QUERY] thread_id\n\nEach connection to mysqld runs in a separate thread. You can see which\nthreads are running with the SHOW PROCESSLIST statement and kill a\nthread with the KILL thread_id statement.\n\nIn MySQL 5.0.0, KILL allows the optional CONNECTION or QUERY modifier:\n\no KILL CONNECTION is the same as KILL with no modifier: It terminates\n  the connection associated with the given thread_id.\n\no KILL QUERY terminates the statement that the connection is currently\n  executing, but leaves the connection itself intact.\n\nIf you have the PROCESS privilege, you can see all threads. If you have\nthe SUPER privilege, you can kill all threads and statements.\nOtherwise, you can see and kill only your own threads and statements.\n\nYou can also use the mysqladmin processlist and mysqladmin kill\ncommands to examine and kill threads.\n\nNote: You cannot use KILL with the Embedded MySQL Server library,\nbecause the embedded server merely runs inside the threads of the host\napplication. It does not create any connection threads of its own.\n','','kill'),(156,'ASTEXT',3,'AsText(g)\n\nConverts a value in internal geometry format to its WKT representation\nand returns the string result.\n','mysql> SET @g = \'LineString(1 1,2 2,3 3)\';\nmysql> SELECT AsText(GeomFromText(@g));\n+--------------------------+\n| AsText(GeomFromText(@g)) |\n+--------------------------+\n| LINESTRING(1 1,2 2,3 3)  |\n+--------------------------+\n','functions-to-convert-geometries-between-formats'),(157,'LPAD',33,'Syntax:\nLPAD(str,len,padstr)\n\nReturns the string str, left-padded with the string padstr to a length\nof len characters. If str is longer than len, the return value is\nshortened to len characters.\n\n','mysql> SELECT LPAD(\'hi\',4,\'??\');\n        -> \'??hi\'\nmysql> SELECT LPAD(\'hi\',1,\'??\');\n        -> \'h\'\n','string-functions'),(158,'RESTORE TABLE',19,'Syntax:\nRESTORE TABLE tbl_name [, tbl_name] ... FROM \'/path/to/backup/directory\'\n\nRESTORE TABLE restores the table or tables from a backup that was made\nwith BACKUP TABLE. Existing tables are not overwritten; if you try to\nrestore over an existing table, an error occurs. Just as for BACKUP\nTABLE, RESTORE TABLE currently works only for MyISAM tables. The\ndirectory should be specified as a full pathname.\n\nThe backup for each table consists of its .frm format file and .MYD\ndata file. The restore operation restores those files, and then uses\nthem to rebuild the .MYI index file. Restoring takes longer than\nbacking up due to the need to rebuild the indexes. The more indexes the\ntable has, the longer it takes.\n','','restore-table'),(159,'DECLARE CONDITION',35,'Syntax:\nDECLARE condition_name CONDITION FOR condition_value\n\ncondition_value:\n    SQLSTATE [VALUE] sqlstate_value\n  | mysql_error_code\n\nThis statement specifies conditions that need specific handling. It\nassociates a name with a specified error condition. The name can\nsubsequently be used in a DECLARE HANDLER statement. See\n[declare-handlers].\n\nA condition_value can be an SQLSTATE value or a MySQL error code.\n','','declare-conditions'),(160,'OVERLAPS',26,'Overlaps(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 spatially overlaps g2. The term\nspatially overlaps is used if two geometries intersect and their\nintersection results in a geometry of the same dimension but not equal\nto either of the given geometries.\n','','functions-that-test-spatial-relationships-between-geometries'),(161,'NUMGEOMETRIES',23,'NumGeometries(gc)\n\nReturns the number of geometries in the GeometryCollection value gc.\n','mysql> SET @gc = \'GeometryCollection(Point(1 1),LineString(2 2, 3 3))\';\nmysql> SELECT NumGeometries(GeomFromText(@gc));\n+----------------------------------+\n| NumGeometries(GeomFromText(@gc)) |\n+----------------------------------+\n|                                2 |\n+----------------------------------+\n','geometrycollection-property-functions'),(162,'SET GLOBAL SQL_SLAVE_SKIP_COUNTER',25,'Syntax:\nSET GLOBAL SQL_SLAVE_SKIP_COUNTER = N\n\nThis statement skips the next N events from the master. This is useful\nfor recovering from replication stops caused by a statement.\n\nThis statement is valid only when the slave thread is not running.\nOtherwise, it produces an error.\n','','set-global-sql-slave-skip-counter'),(163,'MONTHNAME',28,'Syntax:\nMONTHNAME(date)\n\nReturns the full name of the month for date.\n','mysql> SELECT MONTHNAME(\'1998-02-05\');\n        -> \'February\'\n','date-and-time-functions'),(164,'MBREQUAL',5,'MBREqual(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangles of\nthe two geometries g1 and g2 are the same.\n','','relations-on-geometry-mbr'),(165,'CHANGE MASTER TO',25,'Syntax:\nCHANGE MASTER TO master_def [, master_def] ...\n\nmaster_def:\n    MASTER_HOST = \'host_name\'\n  | MASTER_USER = \'user_name\'\n  | MASTER_PASSWORD = \'password\'\n  | MASTER_PORT = port_num\n  | MASTER_CONNECT_RETRY = count\n  | MASTER_LOG_FILE = \'master_log_name\'\n  | MASTER_LOG_POS = master_log_pos\n  | RELAY_LOG_FILE = \'relay_log_name\'\n  | RELAY_LOG_POS = relay_log_pos\n  | MASTER_SSL = {0|1}\n  | MASTER_SSL_CA = \'ca_file_name\'\n  | MASTER_SSL_CAPATH = \'ca_directory_name\'\n  | MASTER_SSL_CERT = \'cert_file_name\'\n  | MASTER_SSL_KEY = \'key_file_name\'\n  | MASTER_SSL_CIPHER = \'cipher_list\'\n\nCHANGE MASTER TO changes the parameters that the slave server uses for\nconnecting to and communicating with the master server. It also updates\nthe contents of the master.info and relay-log.info files.\n\nMASTER_USER, MASTER_PASSWORD, MASTER_SSL, MASTER_SSL_CA,\nMASTER_SSL_CAPATH, MASTER_SSL_CERT, MASTER_SSL_KEY, and\nMASTER_SSL_CIPHER provide information to the slave about how to connect\nto its master.\n\nThe SSL options (MASTER_SSL, MASTER_SSL_CA, MASTER_SSL_CAPATH,\nMASTER_SSL_CERT, MASTER_SSL_KEY, and MASTER_SSL_CIPHER) can be changed\neven on slaves that are compiled without SSL support. They are saved to\nthe master.info file, but are ignored unless you use a server that has\nSSL support enabled.\n\nIf you don\'t specify a given parameter, it keeps its old value, except\nas indicated in the following discussion. For example, if the password\nto connect to your MySQL master has changed, you just need to issue\nthese statements to tell the slave about the new password:\n\nSTOP SLAVE; -- if replication was running\nCHANGE MASTER TO MASTER_PASSWORD=\'new3cret\';\nSTART SLAVE; -- if you want to restart replication\n\nThere is no need to specify the parameters that do not change (host,\nport, user, and so forth).\n\nMASTER_HOST and MASTER_PORT are the hostname (or IP address) of the\nmaster host and its TCP/IP port. Note that if MASTER_HOST is equal to\nlocalhost, then, like in other parts of MySQL, the port number might be\nignored (if Unix socket files can be used, for example).\n\nIf you specify MASTER_HOST or MASTER_PORT, the slave assumes that the\nmaster server is different from before (even if you specify a host or\nport value that is the same as the current value.) In this case, the\nold values for the master binary log name and position are considered\nno longer applicable, so if you do not specify MASTER_LOG_FILE and\nMASTER_LOG_POS in the statement, MASTER_LOG_FILE=\'\' and\nMASTER_LOG_POS=4 are silently appended to it.\n\nMASTER_LOG_FILE and MASTER_LOG_POS are the coordinates at which the\nslave I/O thread should begin reading from the master the next time the\nthread starts. If you specify either of them, you cannot specify\nRELAY_LOG_FILE or RELAY_LOG_POS. If neither of MASTER_LOG_FILE or\nMASTER_LOG_POS are specified, the slave uses the last coordinates of\nthe slave SQL thread before CHANGE MASTER was issued. This ensures that\nthere is no discontinuity in replication, even if the slave SQL thread\nwas late compared to the slave I/O thread, when you merely want to\nchange, say, the password to use.\n\nCHANGE MASTER deletes all relay log files and starts a new one, unless\nyou specify RELAY_LOG_FILE or RELAY_LOG_POS. In that case, relay logs\nare kept; the relay_log_purge global variable is set silently to 0.\n\nCHANGE MASTER is useful for setting up a slave when you have the\nsnapshot of the master and have recorded the log and the offset\ncorresponding to it. After loading the snapshot into the slave, you can\nrun CHANGE MASTER TO MASTER_LOG_FILE=\'log_name_on_master\',\nMASTER_LOG_POS=log_offset_on_master on the slave.\n\nThe following example changes the master and master\'s binary log\ncoordinates. This is used when you want to set up the slave to\nreplicate the master:\n\nCHANGE MASTER TO\n  MASTER_HOST=\'master2.mycompany.com\',\n  MASTER_USER=\'replication\',\n  MASTER_PASSWORD=\'bigs3cret\',\n  MASTER_PORT=3306,\n  MASTER_LOG_FILE=\'master2-bin.001\',\n  MASTER_LOG_POS=4,\n  MASTER_CONNECT_RETRY=10;\n\nThe next example shows an operation that is less frequently employed.\nIt is used when the slave has relay logs that you want it to execute\nagain for some reason. To do this, the master need not be reachable.\nYou need only use CHANGE MASTER TO and start the SQL thread (START\nSLAVE SQL_THREAD):\n\nCHANGE MASTER TO\n  RELAY_LOG_FILE=\'slave-relay-bin.006\',\n  RELAY_LOG_POS=4025;\n','','change-master-to'),(166,'DROP DATABASE',36,'Syntax:\nDROP {DATABASE | SCHEMA} [IF EXISTS] db_name\n\nDROP DATABASE drops all tables in the database and deletes the\ndatabase. Be very careful with this statement! To use DROP DATABASE,\nyou need the DROP privilege on the database. DROP SCHEMA is a synonym\nfor DROP DATABASE as of MySQL 5.0.2.\n\nIF EXISTS is used to prevent an error from occurring if the database\ndoes not exist.\n','','drop-database'),(167,'TIMESTAMP FUNCTION',28,'Syntax:\nTIMESTAMP(expr), TIMESTAMP(expr,expr2)\n\nWith a single argument, this function returns the date or datetime\nexpression expr as a datetime value. With two arguments, it adds the\ntime expression expr2 to the date or datetime expression expr and\nreturns the result as a datetime value.\n','mysql> SELECT TIMESTAMP(\'2003-12-31\');\n        -> \'2003-12-31 00:00:00\'\nmysql> SELECT TIMESTAMP(\'2003-12-31 12:00:00\',\'12:00:00\');\n        -> \'2004-01-01 00:00:00\'\n','date-and-time-functions'),(168,'CHARACTER_LENGTH',33,'Syntax:\nCHARACTER_LENGTH(str)\n\nCHARACTER_LENGTH() is a synonym for CHAR_LENGTH().\n','','string-functions'),(169,'SHOW GRANTS',25,'Syntax:\nSHOW GRANTS FOR user\n\nThis statement lists the GRANT statement or statements that must be\nissued to duplicate the privileges that are granted to a MySQL user\naccount. The account is named using the same format as for the GRANT\nstatement; for example, \'jeffrey\'@\'localhost\'. The user and host parts\nof the account name correspond to the User and Host column values of\nthe user table row for the account.\n\nmysql> SHOW GRANTS FOR \'root\'@\'localhost\';\n+---------------------------------------------------------------------+\n| Grants for root@localhost                                           |\n+---------------------------------------------------------------------+\n| GRANT ALL PRIVILEGES ON *.* TO \'root\'@\'localhost\' WITH GRANT OPTION |\n+---------------------------------------------------------------------+\n\nTo list the privileges granted to the account that you are using to\nconnect to the server, you can use any of the following statements:\n\nSHOW GRANTS;\nSHOW GRANTS FOR CURRENT_USER;\nSHOW GRANTS FOR CURRENT_USER();\n','','show-grants'),(170,'SHOW PRIVILEGES',25,'Syntax:\nSHOW PRIVILEGES\n\nSHOW PRIVILEGES shows the list of system privileges that the MySQL\nserver supports. The exact list of privileges depends on the version of\nyour server.\n','','show-privileges'),(171,'INSERT FUNCTION',33,'Syntax:\nINSERT(str,pos,len,newstr)\n\nReturns the string str, with the substring beginning at position pos\nand len characters long replaced by the string newstr. Returns the\noriginal string if pos is not within the length of the string. Replaces\nthe rest of the string from position pos is len is not within the\nlength of the rest of the string. Returns NULL if any argument is NULL.\n','mysql> SELECT INSERT(\'Quadratic\', 3, 4, \'What\');\n        -> \'QuWhattic\'\nmysql> SELECT INSERT(\'Quadratic\', -1, 4, \'What\');\n        -> \'Quadratic\'\nmysql> SELECT INSERT(\'Quadratic\', 3, 100, \'What\');\n        -> \'QuWhat\'\n','string-functions'),(172,'CRC32',4,'Syntax:\nCRC32(expr)\n\nComputes a cyclic redundancy check value and returns a 32-bit unsigned\nvalue. The result is NULL if the argument is NULL. The argument is\nexpected to be a string and (if possible) is treated as one if it is\nnot.\n','mysql> SELECT CRC32(\'MySQL\');\n        -> 3259397556\nmysql> SELECT CRC32(\'mysql\');\n        -> 2501908538\n','mathematical-functions'),(173,'XOR',12,'Syntax:\nXOR\n\nLogical XOR. Returns NULL if either operand is NULL. For non-NULL\noperands, evaluates to 1 if an odd number of operands is non-zero,\notherwise 0 is returned.\n','mysql> SELECT 1 XOR 1;\n        -> 0\nmysql> SELECT 1 XOR 0;\n        -> 1\nmysql> SELECT 1 XOR NULL;\n        -> NULL\nmysql> SELECT 1 XOR 1 XOR 1;\n        -> 1\n','logical-operators'),(174,'STARTPOINT',11,'StartPoint(ls)\n\nReturns the Point that is the start point of the LineString value ls.\n','mysql> SET @ls = \'LineString(1 1,2 2,3 3)\';\nmysql> SELECT AsText(StartPoint(GeomFromText(@ls)));\n+---------------------------------------+\n| AsText(StartPoint(GeomFromText(@ls))) |\n+---------------------------------------+\n| POINT(1 1)                            |\n+---------------------------------------+\n','linestring-property-functions'),(175,'DECLARE VARIABLE',35,'Syntax:\nDECLARE var_name[,...] type [DEFAULT value]\n\nThis statement is used to declare local variables. To provide a default\nvalue for the variable, include a DEFAULT clause. The value can be\nspecified as an expression; it need not be a constant. If the DEFAULT\nclause is missing, the initial value is NULL.\n\nLocal variables are treated like routine parameters with respect to\ndata type and overflow checking. See [create-procedure].\n\nThe scope of a local variable is within the BEGIN ... END block where\nit is declared. The variable can be referred to in blocks nested within\nthe declaring block, except those blocks that declare a variable with\nthe same name.\n','','declare-local-variables'),(176,'MPOLYFROMTEXT',3,'MPolyFromText(wkt[,srid]), MultiPolygonFromText(wkt[,srid])\n\nConstructs a MULTIPOLYGON value using its WKT representation and SRID.\n','','gis-wkt-functions'),(177,'GRANT',8,'Syntax:\nGRANT priv_type [(column_list)] [, priv_type [(column_list)]] ...\n    ON [object_type] {tbl_name | * | *.* | db_name.*}\n    TO user [IDENTIFIED BY [PASSWORD] \'password\']\n        [, user [IDENTIFIED BY [PASSWORD] \'password\']] ...\n    [REQUIRE\n        NONE |\n        [{SSL| X509}]\n        [CIPHER \'cipher\' [AND]]\n        [ISSUER \'issuer\' [AND]]\n        [SUBJECT \'subject\']]\n    [WITH with_option [with_option] ...]\n\nobject_type =\n    TABLE\n  | FUNCTION\n  | PROCEDURE\n\nwith_option =\n    GRANT OPTION\n  | MAX_QUERIES_PER_HOUR count\n  | MAX_UPDATES_PER_HOUR count\n  | MAX_CONNECTIONS_PER_HOUR count\n  | MAX_USER_CONNECTIONS count\n\nThe GRANT statement enables system administrators to create MySQL user\naccounts and to grant rights to from accounts. To use GRANT, you must\nhave the GRANT OPTION privilege, and you must have the privileges that\nyou are granting. The REVOKE statement is related and enables\nadministrators to remove account privileges. See [revoke].\n\nMySQL account information is stored in the tables of the mysql\ndatabase. This database and the access control system are discussed\nextensively in [database-administration], which you should consult for\nadditional details.\n\nImportant: Some releases of MySQL introduce changes to the structure of\nthe grant tables to add new privileges or features. Whenever you update\nto a new version of MySQL, you should update your grant tables to make\nsure that they have the current structure so that you can take\nadvantage of any new capabilities. See [mysql-upgrade].\n\nIf the grant tables hold privilege rows that contain mixed-case\ndatabase or table names and the lower_case_table_names system variable\nis set to a non-zero value, REVOKE cannot be used to revoke these\nprivileges. It will be necessary to manipulate the grant tables\ndirectly. (GRANT will not create such rows when lower_case_table_names\nis set, but such rows might have been created prior to setting the\nvariable.)\n\nPrivileges can be granted at several levels:\n\no Global level\n\n  Global privileges apply to all databases on a given server. These\n  privileges are stored in the mysql.user table. GRANT ALL ON *.* and\n  REVOKE ALL ON *.* grant and revoke only global privileges.\n\no Database level\n\n  Database privileges apply to all objects in a given database. These\n  privileges are stored in the mysql.db and mysql.host tables. GRANT\n  ALL ON db_name.* and REVOKE ALL ON db_name.* grant and revoke only\n  database privileges.\n\no Table level\n\n  Table privileges apply to all columns in a given table. These\n  privileges are stored in the mysql.tables_priv table. GRANT ALL ON\n  db_name.tbl_name and REVOKE ALL ON db_name.tbl_name grant and revoke\n  only table privileges.\n\no Column level\n\n  Column privileges apply to single columns in a given table. These\n  privileges are stored in the mysql.columns_priv table. When using\n  REVOKE, you must specify the same columns that were granted.\n\no Routine level\n\n  The CREATE ROUTINE, ALTER ROUTINE, EXECUTE, and GRANT privileges\n  apply to stored routines (functions and procedures). They can be\n  granted at the global and database levels. Also, except for CREATE\n  ROUTINE, these privileges can be granted at the routine level for\n  individual routines and are stored in the mysql.procs_priv table.\n\nThe object_type clause was added in MySQL 5.0.6. It should be specified\nas TABLE, FUNCTION, or PROCEDURE when the following object is a table,\na stored function, or a stored procedure.\n','','grant'),(178,'MBRINTERSECTS',5,'MBRIntersects(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangles of\nthe two geometries g1 and g2 intersect.\n','','relations-on-geometry-mbr'),(179,'BIT_OR',14,'Syntax:\nBIT_OR(expr)\n\nReturns the bitwise OR of all bits in expr. The calculation is\nperformed with 64-bit (BIGINT) precision.\n','','group-by-functions'),(180,'YEARWEEK',28,'Syntax:\nYEARWEEK(date), YEARWEEK(date,start)\n\nReturns year and week for a date. The start argument works exactly like\nthe start argument to WEEK(). The year in the result may be different\nfrom the year in the date argument for the first and the last week of\nthe year.\n','mysql> SELECT YEARWEEK(\'1987-01-01\');\n        -> 198653\n','date-and-time-functions'),(181,'NOT BETWEEN',17,'Syntax:\nexpr NOT BETWEEN min AND max\n\nThis is the same as NOT (expr BETWEEN min AND max).\n','','comparison-operators'),(182,'LOG10',4,'Syntax:\nLOG10(X)\n\nReturns the base-10 logarithm of X.\n','mysql> SELECT LOG10(2);\n        -> 0.30102999566398\nmysql> SELECT LOG10(100);\n        -> 2\nmysql> SELECT LOG10(-100);\n        -> NULL\n','mathematical-functions'),(183,'SQRT',4,'Syntax:\nSQRT(X)\n\nReturns the square root of a non-negative number X.\n','mysql> SELECT SQRT(4);\n        -> 2\nmysql> SELECT SQRT(20);\n        -> 4.4721359549996\nmysql> SELECT SQRT(-16);\n        -> NULL        \n','mathematical-functions'),(184,'DECIMAL',20,'DECIMAL[(M[,D])] [UNSIGNED] [ZEROFILL]\n\nFor MySQL 5.0.3 and above:\n\nA packed \"exact\" fixed-point number. M is the total number of decimal\ndigits (the precision) and D is the number of digits after the decimal\npoint (the scale). The decimal point and (for negative numbers) the `-\'\nsign are not counted in M. If D is 0, values have no decimal point or\nfractional part. The maximum number of digits (M) for DECIMAL is 65 (64\nfrom 5.0.3 to 5.0.5). The maximum number of supported decimals (D) is\n30. If D is omitted, the default is 0. If M is omitted, the default is\n10.\n\nUNSIGNED, if specified, disallows negative values.\n\nAll basic calculations (+, -, *, /) with DECIMAL columns are done with\na precision of 65 digits.\n\nBefore MySQL 5.0.3:\n\nAn unpacked fixed-point number. Behaves like a CHAR column; \"unpacked\"\nmeans the number is stored as a string, using one character for each\ndigit of the value. M is the total number of digits and D is the number\nof digits after the decimal point. The decimal point and (for negative\nnumbers) the `-\' sign are not counted in M, although space for them is\nreserved. If D is 0, values have no decimal point or fractional part.\nThe maximum range of DECIMAL values is the same as for DOUBLE, but the\nactual range for a given DECIMAL column may be constrained by the\nchoice of M and D. If D is omitted, the default is 0. If M is omitted,\nthe default is 10.\n\nUNSIGNED, if specified, disallows negative values.\n','','numeric-type-overview'),(185,'CREATE FUNCTION',34,'Syntax:\nCREATE [AGGREGATE] FUNCTION function_name RETURNS {STRING|INTEGER|REAL|DECIMAL}\n    SONAME shared_library_name\n\nA user-defined function (UDF) is a way to extend MySQL with a new\nfunction that works like a native (built-in) MySQL function such as\nABS() or CONCAT().\n\nfunction_name is the name that should be used in SQL statements to\ninvoke the function. The RETURNS clause indicates the type of the\nfunction\'s return value. As of MySQL 5.0.3, DECIMAL is a legal value\nafter RETURNS, but currently DECIMAL functions return string values and\nshould be written like STRING functions.\n\nshared_library_name is the basename of the shared object file that\ncontains the code that implements the function. The file must be\nlocated in a directory that is searched by your system\'s dynamic\nlinker.\n\nTo create a function, you must have the INSERT and privilege for the\nmysql database. This is necessary because CREATE FUNCTION adds a row to\nthe mysql.func system table that records the function\'s name, type, and\nshared library name. If you do not have this table, you should run the\nmysql_upgrade command to create it. See [mysql-upgrade].\n','','create-function'),(186,'GEOMETRYN',23,'GeometryN(gc,N)\n\nReturns the N-th geometry in the GeometryCollection value gc.\nGeometries are numbered beginning with 1.\n','mysql> SET @gc = \'GeometryCollection(Point(1 1),LineString(2 2, 3 3))\';\nmysql> SELECT AsText(GeometryN(GeomFromText(@gc),1));\n+----------------------------------------+\n| AsText(GeometryN(GeomFromText(@gc),1)) |\n+----------------------------------------+\n| POINT(1 1)                             |\n+----------------------------------------+\n','geometrycollection-property-functions'),(187,'CREATE INDEX',36,'Syntax:\nCREATE [UNIQUE|FULLTEXT|SPATIAL] INDEX index_name\n    [USING index_type]\n    ON tbl_name (index_col_name,...)\n\nindex_col_name:\n    col_name [(length)] [ASC | DESC]\n\nCREATE INDEX is mapped to an ALTER TABLE statement to create indexes.\nSee [alter-table]. For more information about how MySQL uses indexes,\nsee [mysql-indexes].\n','','create-index'),(188,'ALTER DATABASE',36,'Syntax:\nALTER {DATABASE | SCHEMA} [db_name]\n    alter_specification [, alter_specification] ...\n\nalter_specification:\n    [DEFAULT] CHARACTER SET charset_name\n  | [DEFAULT] COLLATE collation_name\n\nALTER DATABASE enables you to change the overall characteristics of a\ndatabase. These characteristics are stored in the db.opt file in the\ndatabase directory. To use ALTER DATABASE, you need the ALTER privilege\non the database. ALTER SCHEMA is a synonym for ALTER DATABASE as of\nMySQL 5.0.2.\n\nThe CHARACTER SET clause changes the default database character set.\nThe COLLATE clause changes the default database collation. [charset],\ndiscusses character set and collation names.\n\nThe database name can be omitted, in which case the statement applies\nto the default database.\n','','alter-database'),(189,'<<',18,'Syntax:\n<<\n\nShifts a longlong (BIGINT) number to the left.\n','mysql> SELECT 1 << 2;\n        -> 4\n','bit-functions'),(190,'SHOW TABLE STATUS',25,'Syntax:\nSHOW TABLE STATUS [FROM db_name] [LIKE \'pattern\']\n\nSHOW TABLE STATUS works likes SHOW TABLE, but provides a lot of\ninformation about each table. You can also get this list using the\nmysqlshow --status db_name command.\n','','show-table-status'),(191,'MD5',10,'Syntax:\nMD5(str)\n\nCalculates an MD5 128-bit checksum for the string. The value is\nreturned as a binary string of 32 hex digits, or NULL if the argument\nwas NULL. The return value can, for example, be used as a hash key.\n','mysql> SELECT MD5(\'testing\');\n        -> \'ae2b1fca515949e5d54fb22b8ed95575\'\n','encryption-functions'),(192,'<',17,'Syntax:\n<\n\nLess than:\n','mysql> SELECT 2 < 2;\n        -> 0\n','comparison-operators'),(193,'UNIX_TIMESTAMP',28,'Syntax:\nUNIX_TIMESTAMP(), UNIX_TIMESTAMP(date)\n\nIf called with no argument, returns a Unix timestamp (seconds since\n\'1970-01-01 00:00:00\' UTC) as an unsigned integer. If UNIX_TIMESTAMP()\nis called with a date argument, it returns the value of the argument as\nseconds since \'1970-01-01 00:00:00\' UTC. date may be a DATE string, a\nDATETIME string, a TIMESTAMP, or a number in the format YYMMDD or\nYYYYMMDD. The server interprets date as a value in the current time\nzone and converts it to an internal value in UTC. Clients can set their\ntime zone as described in [time-zone-support].\n','mysql> SELECT UNIX_TIMESTAMP();\n        -> 882226357\nmysql> SELECT UNIX_TIMESTAMP(\'1997-10-04 22:23:00\');\n        -> 875996580\n','date-and-time-functions'),(194,'DAYOFMONTH',28,'Syntax:\nDAYOFMONTH(date)\n\nReturns the day of the month for date, in the range 0 to 31.\n','mysql> SELECT DAYOFMONTH(\'1998-02-03\');\n        -> 3\n','date-and-time-functions'),(195,'ASCII',33,'Syntax:\nASCII(str)\n\nReturns the numeric value of the leftmost character of the string str.\nReturns 0 if str is the empty string. Returns NULL if str is NULL.\nASCII() works for characters with numeric values from 0 to 255.\n','mysql> SELECT ASCII(\'2\');\n        -> 50\nmysql> SELECT ASCII(2);\n        -> 50\nmysql> SELECT ASCII(\'dx\');\n        -> 100\n','string-functions'),(196,'DIV',4,'Syntax:\nDIV\n\nInteger division. Similar to FLOOR(), but is safe with BIGINT values.\n','mysql> SELECT 5 DIV 2;\n        -> 2\n','arithmetic-functions'),(197,'RENAME USER',8,'Syntax:\nRENAME USER old_user TO new_user\n    [, old_user TO new_user] ...\n\nThe RENAME USER statement renames existing MySQL accounts. To use it,\nyou must have the global CREATE USER privilege or the UPDATE privilege\nfor the mysql database. An error occurs if any old account does not\nexist or any new account exists. Each account is named using the same\nformat as for the GRANT statement; for example, \'jeffrey\'@\'localhost\'.\nThe user and host parts of the account name correspond to the User and\nHost column values of the user table row for the account.\n','','rename-user'),(198,'SHOW SLAVE STATUS',25,'Syntax:\nSHOW SLAVE STATUS\n\nThis statement provides status information on essential parameters of\nthe slave threads. If you issue this statement using the mysql client,\nyou can use a \\G statement terminator rather than a semicolon to obtain\na more readable vertical layout:\n\nmysql> SHOW SLAVE STATUS\\G\n*************************** 1. row ***************************\n       Slave_IO_State: Waiting for master to send event\n          Master_Host: localhost\n          Master_User: root\n          Master_Port: 3306\n        Connect_Retry: 3\n      Master_Log_File: gbichot-bin.005\n  Read_Master_Log_Pos: 79\n       Relay_Log_File: gbichot-relay-bin.005\n        Relay_Log_Pos: 548\nRelay_Master_Log_File: gbichot-bin.005\n     Slave_IO_Running: Yes\n    Slave_SQL_Running: Yes\n      Replicate_Do_DB:\n  Replicate_Ignore_DB:\n           Last_Errno: 0\n           Last_Error:\n         Skip_Counter: 0\n  Exec_Master_Log_Pos: 79\n      Relay_Log_Space: 552\n      Until_Condition: None\n       Until_Log_File:\n        Until_Log_Pos: 0\n   Master_SSL_Allowed: No\n   Master_SSL_CA_File:\n   Master_SSL_CA_Path:\n      Master_SSL_Cert:\n    Master_SSL_Cipher:\n       Master_SSL_Key:\nSeconds_Behind_Master: 8\n','','show-slave-status'),(199,'GEOMETRY',30,'MySQL provides a standard way of creating spatial columns for geometry\ntypes, for example, with CREATE TABLE or ALTER TABLE. Currently,\nspatial columns are supported for MyISAM, InnoDB, NDB, BDB, and ARCHIVE\ntables. (Support for storage engines other than MyISAM was added in\nMySQL 5.0.16.) See also the annotations about spatial indexes under\n[creating-spatial-indexes].\n','CREATE TABLE geom (g GEOMETRY);\n','creating-spatial-columns'),(200,'NUMPOINTS',11,'NumPoints(ls)\n\nReturns the number of Point objects in the LineString value ls.\n','mysql> SET @ls = \'LineString(1 1,2 2,3 3)\';\nmysql> SELECT NumPoints(GeomFromText(@ls));\n+------------------------------+\n| NumPoints(GeomFromText(@ls)) |\n+------------------------------+\n|                            3 |\n+------------------------------+\n','linestring-property-functions'),(201,'&',18,'Syntax:\n&\n\nBitwise AND:\n','mysql> SELECT 29 & 15;\n        -> 13\n','bit-functions'),(202,'LOCALTIMESTAMP',28,'Syntax:\nLOCALTIMESTAMP, LOCALTIMESTAMP()\n\nLOCALTIMESTAMP and LOCALTIMESTAMP() are synonyms for NOW().\n','','date-and-time-functions'),(203,'ADDDATE',28,'Syntax:\nADDDATE(date,INTERVAL expr type), ADDDATE(expr,days)\n\nWhen invoked with the INTERVAL form of the second argument, ADDDATE()\nis a synonym for DATE_ADD(). The related function SUBDATE() is a\nsynonym for DATE_SUB(). For information on the INTERVAL argument, see\nthe discussion for DATE_ADD().\n\nmysql> SELECT DATE_ADD(\'1998-01-02\', INTERVAL 31 DAY);\n        -> \'1998-02-02\'\nmysql> SELECT ADDDATE(\'1998-01-02\', INTERVAL 31 DAY);\n        -> \'1998-02-02\'\n\nWhen invoked with the days form of the second argument, MySQL treats it\nas an integer number of days to be added to expr.\n','mysql> SELECT ADDDATE(\'1998-01-02\', 31);\n        -> \'1998-02-02\'\n','date-and-time-functions'),(204,'REPEAT LOOP',35,'Syntax:\n[begin_label:] REPEAT\n    statement_list\nUNTIL search_condition\nEND REPEAT [end_label]\n\nThe statement list within a REPEAT statement is repeated until the\nsearch_condition is true. Thus, a REPEAT always enters the loop at\nleast once. statement_list consists of one or more statements.\n\nA REPEAT statement can be labeled. end_label cannot be given unless\nbegin_label also is present. If both are present, they must be the\nsame.\n','mysql> delimiter //\n\nmysql> CREATE PROCEDURE dorepeat(p1 INT)\n    -> BEGIN\n    ->   SET @x = 0;\n    ->   REPEAT SET @x = @x + 1; UNTIL @x > p1 END REPEAT;\n    -> END\n    -> //\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> CALL dorepeat(1000)//\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> SELECT @x//\n+------+\n| @x   |\n+------+\n| 1001 |\n+------+\n1 row in set (0.00 sec)\n','repeat-statement'),(205,'SMALLINT',20,'SMALLINT[(M)] [UNSIGNED] [ZEROFILL]\n\nA small integer. The signed range is -32768 to 32767. The unsigned\nrange is 0 to 65535.\n','','numeric-type-overview'),(206,'DOUBLE PRECISION',20,'DOUBLE PRECISION[(M,D)] [UNSIGNED] [ZEROFILL], REAL[(M,D)] [UNSIGNED]\n[ZEROFILL]\n\nThese types are synonyms for DOUBLE. Exception: If the REAL_AS_FLOAT\nSQL mode is enabled, REAL is a synonym for FLOAT rather than DOUBLE.\n','','numeric-type-overview'),(207,'ORD',33,'Syntax:\nORD(str)\n\nIf the leftmost character of the string str is a multi-byte character,\nreturns the code for that character, calculated from the numeric values\nof its constituent bytes using this formula:\n\n  (1st byte code)\n+ (2nd byte code Ã— 256)\n+ (3rd byte code Ã— 2562) ...\n\nIf the leftmost character is not a multi-byte character, ORD() returns\nthe same value as the ASCII() function.\n','mysql> SELECT ORD(\'2\');\n        -> 50\n','string-functions'),(208,'ENVELOPE',32,'Envelope(g)\n\nReturns the Minimum Bounding Rectangle (MBR) for the geometry value g.\nThe result is returned as a Polygon value.\n\nThe polygon is defined by the corner points of the bounding box:\n\nPOLYGON((MINX MINY, MAXX MINY, MAXX MAXY, MINX MAXY, MINX MINY))\n','mysql> SELECT AsText(Envelope(GeomFromText(\'LineString(1 1,2 2)\')));\n+-------------------------------------------------------+\n| AsText(Envelope(GeomFromText(\'LineString(1 1,2 2)\'))) |\n+-------------------------------------------------------+\n| POLYGON((1 1,2 1,2 2,1 2,1 1))                        |\n+-------------------------------------------------------+\n','general-geometry-property-functions'),(209,'DEALLOCATE PREPARE',25,'Syntax:\n{DEALLOCATE | DROP} PREPARE stmt_name\n\nTo deallocate a prepared statement, use the DEALLOCATE PREPARE\nstatement. Attempting to execute a prepared statement after\ndeallocating it results in an error.\n\nIf you terminate a client session without deallocating a previously\nprepared statement, the server deallocates it automatically.\n','','sqlps'),(210,'IS_FREE_LOCK',13,'Syntax:\nIS_FREE_LOCK(str)\n\nChecks whether the lock named str is free to use (that is, not locked).\nReturns 1 if the lock is free (no one is using the lock), 0 if the lock\nis in use, and NULL if an error occurs (such as an incorrect argument).\n','','miscellaneous-functions'),(211,'TOUCHES',26,'Touches(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 spatially touches g2. Two\ngeometries spatially touch if the interiors of the geometries do not\nintersect, but the boundary of one of the geometries intersects either\nthe boundary or the interior of the other.\n','','functions-that-test-spatial-relationships-between-geometries'),(212,'INET_ATON',13,'Syntax:\nINET_ATON(expr)\n\nGiven the dotted-quad representation of a network address as a string,\nreturns an integer that represents the numeric value of the address.\nAddresses may be 4- or 8-byte addresses.\n','mysql> SELECT INET_ATON(\'209.207.224.40\');\n        -> 3520061480\n','miscellaneous-functions'),(213,'UNCOMPRESS',10,'Syntax:\nUNCOMPRESS(string_to_uncompress)\n\nUncompresses a string compressed by the COMPRESS() function. If the\nargument is not a compressed value, the result is NULL. This function\nrequires MySQL to have been compiled with a compression library such as\nzlib. Otherwise, the return value is always NULL.\n','mysql> SELECT UNCOMPRESS(COMPRESS(\'any string\'));\n        -> \'any string\'\nmysql> SELECT UNCOMPRESS(\'any string\');\n        -> NULL\n','encryption-functions'),(214,'AUTO_INCREMENT',20,'The AUTO_INCREMENT attribute can be used to generate a unique identity\nfor new rows:\n','CREATE TABLE animals (\n     id MEDIUMINT NOT NULL AUTO_INCREMENT,\n     name CHAR(30) NOT NULL,\n     PRIMARY KEY (id)\n );\n\nINSERT INTO animals (name) VALUES \n    (\'dog\'),(\'cat\'),(\'penguin\'),\n    (\'lax\'),(\'whale\'),(\'ostrich\');\n\nSELECT * FROM animals;\n','example-auto-increment'),(215,'ISSIMPLE',32,'IsSimple(g)\n\nCurrently, this function is a placeholder and should not be used. If\nimplemented, its behavior will be as described in the next paragraph.\n\nReturns 1 if the geometry value g has no anomalous geometric points,\nsuch as self-intersection or self-tangency. IsSimple() returns 0 if the\nargument is not simple, and -1 if it is NULL.\n\nThe description of each instantiable geometric class given earlier in\nthe chapter includes the specific conditions that cause an instance of\nthat class to be classified as not simple. (See\n[gis-geometry-class-hierarchy].)\n','','general-geometry-property-functions'),(216,'- BINARY',4,'Syntax:\n-\n\nSubtraction:\n','mysql> SELECT 3-5;\n        -> -2\n','arithmetic-functions'),(217,'GEOMCOLLFROMTEXT',3,'GeomCollFromText(wkt[,srid]), GeometryCollectionFromText(wkt[,srid])\n\nConstructs a GEOMETRYCOLLECTION value using its WKT representation and\nSRID.\n','','gis-wkt-functions'),(218,'WKT DEFINITION',3,'The Well-Known Text (WKT) representation of Geometry is designed to\nexchange geometry data in ASCII form.\n','','gis-wkt-format'),(219,'CURRENT_TIME',28,'Syntax:\nCURRENT_TIME, CURRENT_TIME()\n\nCURRENT_TIME and CURRENT_TIME() are synonyms for CURTIME().\n','','date-and-time-functions'),(220,'REVOKE',8,'Syntax:\nREVOKE priv_type [(column_list)] [, priv_type [(column_list)]] ...\n    ON [object_type] {tbl_name | * | *.* | db_name.*}\n    FROM user [, user] ...\n\nREVOKE ALL PRIVILEGES, GRANT OPTION FROM user [, user] ...\n\nThe REVOKE statement enables system administrators to revoke privileges\nfrom MySQL accounts. To use REVOKE, you must have the GRANT OPTION\nprivilege, and you must have the privileges that you are revoking.\n\nFor details on the levels at which privileges exist, the allowable\npriv_type values, and the syntax for specifying users and passwords,\nsee [grant]\n','','revoke'),(221,'LAST_INSERT_ID',15,'Syntax:\nLAST_INSERT_ID(), LAST_INSERT_ID(expr)\n\nReturns the first automatically generated value that was set for an\nAUTO_INCREMENT column by the most recent INSERT or UPDATE statement to\naffect such a column.\n','mysql> SELECT LAST_INSERT_ID();\n        -> 195\n','information-functions'),(222,'LAST_DAY',28,'Syntax:\nLAST_DAY(date)\n\nTakes a date or datetime value and returns the corresponding value for\nthe last day of the month. Returns NULL if the argument is invalid.\n','mysql> SELECT LAST_DAY(\'2003-02-05\');\n        -> \'2003-02-28\'\nmysql> SELECT LAST_DAY(\'2004-02-05\');\n        -> \'2004-02-29\'\nmysql> SELECT LAST_DAY(\'2004-01-01 01:01:01\');\n        -> \'2004-01-31\'\nmysql> SELECT LAST_DAY(\'2003-03-32\');\n        -> NULL\n','date-and-time-functions'),(223,'MEDIUMINT',20,'MEDIUMINT[(M)] [UNSIGNED] [ZEROFILL]\n\nA medium-sized integer. The signed range is -8388608 to 8388607. The\nunsigned range is 0 to 16777215.\n','','numeric-type-overview'),(224,'FLOOR',4,'Syntax:\nFLOOR(X)\n\nReturns the largest integer value not greater than X.\n','mysql> SELECT FLOOR(1.23);\n        -> 1\nmysql> SELECT FLOOR(-1.23);\n        -> -2\n','mathematical-functions'),(225,'RTRIM',33,'Syntax:\nRTRIM(str)\n\nReturns the string str with trailing space characters removed.\n','mysql> SELECT RTRIM(\'barbar   \');\n        -> \'barbar\'\n','string-functions'),(226,'DEGREES',4,'Syntax:\nDEGREES(X)\n\nReturns the argument X, converted from radians to degrees.\n','mysql> SELECT DEGREES(PI());\n        -> 180\nmysql> SELECT DEGREES(PI() / 2);\n        -> 90\n','mathematical-functions'),(227,'EXPLAIN',25,'Syntax:\nEXPLAIN tbl_name\n\nOr:\n\nEXPLAIN [EXTENDED] SELECT select_options\n\nThe EXPLAIN statement can be used either as a synonym for DESCRIBE or\nas a way to obtain information about how MySQL executes a SELECT\nstatement:\n\no EXPLAIN tbl_name is synonymous with DESCRIBE tbl_name or SHOW COLUMNS\n  FROM tbl_name.\n\no When you precede a SELECT statement with the keyword EXPLAIN, MySQL\n  displays information from the optimizer about the query execution\n  plan. That is, MySQL explains how it would process the SELECT,\n  including information about how tables are joined and in which order.\n','','explain'),(228,'VARCHAR',20,'[NATIONAL] VARCHAR(M) [BINARY]\n\nA variable-length string. M represents the maximum column length. In\nMySQL 5.0, the range of M is 0 to 255 before MySQL 5.0.3, and 0 to\n65,535 in MySQL 5.0.3 and later. (The actual maximum length of a\nVARCHAR in MySQL 5.0 is determined by the maximum row size and the\ncharacter set you use. The maximum effective length starting with MySQL\n5.0.3 is 65,532 bytes.)\n\nNote: Before 5.0.3, trailing spaces were removed when VARCHAR values\nwere stored, which differs from the standard SQL specification.\n\nPrior to MySQL 5.0.3, a VARCHAR column with a length specification\ngreater than 255 was converted to the smallest TEXT type that could\nhold values of the given length. For example, VARCHAR(500) was\nconverted to TEXT, and VARCHAR(200000) was converted to MEDIUMTEXT.\nThis was a compatibility feature. However, this conversion affected\ntrailing-space removal.\n\nVARCHAR is shorthand for CHARACTER VARYING.\n\nThe BINARY attribute is shorthand for specifying the binary collation\nof the column character set. In this case, sorting and comparison are\nbased on numeric character values.\n\nVARCHAR values are stored using as many characters as are needed, plus\none byte to record the length (two bytes for columns that are declared\nwith a length longer than 255).\n','','string-type-overview'),(229,'UNHEX',33,'Syntax:\n\nUNHEX(str)\n\nPerforms the inverse operation of HEX(str). That is, it interprets each\npair of hexadecimal digits in the argument as a number and converts it\nto the character represented by the number. The resulting characters\nare returned as a binary string.\n','mysql> SELECT UNHEX(\'4D7953514C\');\n        -> \'MySQL\'\nmysql> SELECT 0x4D7953514C;\n        -> \'MySQL\'\nmysql> SELECT UNHEX(HEX(\'string\'));\n        -> \'string\'\nmysql> SELECT HEX(UNHEX(\'1267\'));\n        -> \'1267\'\n','string-functions'),(230,'- UNARY',4,'Syntax:\n-\n\nUnary minus. This operator changes the sign of the argument.\n','mysql> SELECT - 2;\n        -> -2\n','arithmetic-functions'),(231,'SELECT INTO',35,'Syntax:\nSELECT col_name[,...] INTO var_name[,...] table_expr\n\nThis SELECT syntax stores selected columns directly into variables.\nTherefore, only a single row may be retrieved.\n','SELECT id,data INTO x,y FROM test.t1 LIMIT 1;\n','select-into-statement'),(232,'COS',4,'Syntax:\nCOS(X)\n\nReturns the cosine of X, where X is given in radians.\n','mysql> SELECT COS(PI());\n        -> -1\n','mathematical-functions'),(233,'DATE FUNCTION',28,'Syntax:\nDATE(expr)\n\nExtracts the date part of the date or datetime expression expr.\n','mysql> SELECT DATE(\'2003-12-31 01:02:03\');\n        -> \'2003-12-31\'\n','date-and-time-functions'),(234,'DROP TRIGGER',21,'Syntax:\nDROP TRIGGER [schema_name.]trigger_name\n\nThis statement drops a trigger. The schema (database) name is optional.\nIf the schema is omitted, the trigger is dropped from the default\nschema. DROP TRIGGER was added in MySQL 5.0.2. Its use requires the\nSUPER privilege.\n','','drop-trigger'),(235,'RESET MASTER',25,'Syntax:\nRESET MASTER\n\nDeletes all binary logs listed in the index file, resets the binary log\nindex file to be empty, and creates a new binary log file.\n','','reset-master'),(236,'TAN',4,'Syntax:\nTAN(X)\n\nReturns the tangent of X, where X is given in radians.\n','mysql> SELECT TAN(PI());\n        -> -1.2246063538224e-16\nmysql> SELECT TAN(PI()+1);\n        -> 1.5574077246549\n','mathematical-functions'),(237,'PI',4,'Syntax:\nPI()\n\nReturns the value of Ï€ (pi). The default number of decimal places\ndisplayed is seven, but MySQL uses the full double-precision value\ninternally.\n','mysql> SELECT PI();\n        -> 3.141593\nmysql> SELECT PI()+0.000000000000000000;\n        -> 3.141592653589793116\n','mathematical-functions'),(238,'WEEKOFYEAR',28,'Syntax:\nWEEKOFYEAR(date)\n\nReturns the calendar week of the date as a number in the range from 1\nto 53. WEEKOFYEAR() is a compatibility function that is equivalent to\nWEEK(date,3).\n','mysql> SELECT WEEKOFYEAR(\'1998-02-20\');\n        -> 8\n','date-and-time-functions'),(239,'/',4,'Syntax:\n/\n\nDivision:\n','mysql> SELECT 3/5;\n        -> 0.60\n','arithmetic-functions'),(240,'STDDEV_SAMP',14,'Syntax:\nSTDDEV_SAMP(expr)\n\nReturns the sample standard deviation of expr (the square root of\nVAR_SAMP(). This function was added in MySQL 5.0.3.\n\nSTDDEV_SAMP() returns NULL if there were no matching rows.\n','','group-by-functions'),(241,'SCHEMA',15,'Syntax:\nSCHEMA()\n\nThis function is a synonym for DATABASE(). It was added in MySQL 5.0.2.\n','','information-functions'),(242,'MLINEFROMWKB',29,'MLineFromWKB(wkb[,srid]), MultiLineStringFromWKB(wkb[,srid])\n\nConstructs a MULTILINESTRING value using its WKB representation and\nSRID.\n','','gis-wkb-functions'),(243,'LOG2',4,'Syntax:\nLOG2(X)\n\nReturns the base-2 logarithm of X.\n','mysql> SELECT LOG2(65536);\n        -> 16\nmysql> SELECT LOG2(-100);\n        -> NULL\n','mathematical-functions'),(244,'SUBTIME',28,'Syntax:\nSUBTIME(expr,expr2)\n\nSUBTIME() subtracts expr2 from expr and returns the result. expr is a\ntime or datetime expression, and expr2 is a time expression.\n','mysql> SELECT SUBTIME(\'1997-12-31 23:59:59.999999\',\'1 1:1:1.000002\');\n        -> \'1997-12-30 22:58:58.999997\'\nmysql> SELECT SUBTIME(\'01:00:00.999999\', \'02:00:00.999998\');\n        -> \'-00:59:59.999999\'\n','date-and-time-functions'),(245,'UNCOMPRESSED_LENGTH',10,'Syntax:\nUNCOMPRESSED_LENGTH(compressed_string)\n\nReturns the length that the compressed string had before being\ncompressed.\n','mysql> SELECT UNCOMPRESSED_LENGTH(COMPRESS(REPEAT(\'a\',30)));\n        -> 30\n','encryption-functions'),(246,'DROP TABLE',36,'Syntax:\nDROP [TEMPORARY] TABLE [IF EXISTS]\n    tbl_name [, tbl_name] ...\n    [RESTRICT | CASCADE]\n\nDROP TABLE removes one or more tables. You must have the DROP privilege\nfor each table. All table data and the table definition are removed, so\nbe careful with this statement!\n\nUse IF EXISTS to prevent an error from occurring for tables that do not\nexist. A NOTE is generated for each non-existent table when using IF\nEXISTS. See [show-warnings].\n\nRESTRICT and CASCADE are allowed to make porting easier. For the\nmoment, they do nothing.\n\nNote: DROP TABLE automatically commits the current active transaction,\nunless you use the TEMPORARY keyword.\n','','drop-table'),(247,'SHOW CREATE TABLE',25,'Syntax:\nSHOW CREATE TABLE tbl_name\n\nShows the CREATE TABLE statement that creates the given table. As of\nMySQL 5.0.1, this statement also works with views.\nSHOW CREATE TABLE quotes table and column names according to the value\nof the SQL_QUOTE_SHOW_CREATE option. See [set-option].\n','mysql> SHOW CREATE TABLE t\\G\n*************************** 1. row ***************************\n       Table: t\nCreate Table: CREATE TABLE t (\n  id INT(11) default NULL auto_increment,\n  s char(60) default NULL,\n  PRIMARY KEY (id)\n) ENGINE=MyISAM\n','show-create-table'),(248,'DUAL',25,'You are allowed to specify DUAL as a dummy table name in situations\nwhere no tables are referenced:\n\nmysql> SELECT 1 + 1 FROM DUAL;\n        -> 2\n\nDUAL is purely for compatibility with some other database servers that\nrequire a FROM clause. MySQL does not require the clause if no tables\nare referenced.\n','','select'),(249,'INSTR',33,'Syntax:\nINSTR(str,substr)\n\nReturns the position of the first occurrence of substring substr in\nstring str. This is the same as the two-argument form of LOCATE(),\nexcept that the order of the arguments is reversed.\n','mysql> SELECT INSTR(\'foobarbar\', \'bar\');\n        -> 4\nmysql> SELECT INSTR(\'xbar\', \'foobar\');\n        -> 0\n','string-functions'),(250,'NOW',28,'Syntax:\nNOW()\n\nReturns the current date and time as a value in \'YYYY-MM-DD HH:MM:SS\'\nor YYYYMMDDHHMMSS format, depending on whether the function is used in\na string or numeric context.\n','mysql> SELECT NOW();\n        -> \'1997-12-15 23:50:26\'\nmysql> SELECT NOW() + 0;\n        -> 19971215235026\n','date-and-time-functions'),(251,'SHOW ENGINES',25,'Syntax:\nSHOW [STORAGE] ENGINES\n\nSHOW ENGINES displays status information about the server\'s storage\nengines. This is particularly useful for checking whether a storage\nengine is supported, or to see what the default engine is. SHOW TABLE\nTYPES is a deprecated synonym.\n','','show-engines'),(252,'>=',17,'Syntax:\n>=\n\nGreater than or equal:\n','mysql> SELECT 2 >= 2;\n        -> 1\n','comparison-operators'),(253,'EXP',4,'Syntax:\nEXP(X)\n\nReturns the value of e (the base of natural logarithms) raised to the\npower of X.\n','mysql> SELECT EXP(2);\n        -> 7.3890560989307\nmysql> SELECT EXP(-2);\n        -> 0.13533528323661\nmysql> SELECT EXP(0);\n        -> 1\n','mathematical-functions'),(254,'SHA',10,'Syntax:\nSHA1(str), SHA(str)\n\nCalculates an SHA-1 160-bit checksum for the string, as described in\nRFC 3174 (Secure Hash Algorithm). The value is returned as a binary\nstring of 40 hex digits, or NULL if the argument was NULL. One of the\npossible uses for this function is as a hash key. You can also use it\nas a cryptographic function for storing passwords. SHA() is synonymous\nwith SHA1().\n','mysql> SELECT SHA1(\'abc\');\n        -> \'a9993e364706816aba3e25717850c26c9cd0d89d\'\n','encryption-functions'),(255,'LONGBLOB',20,'LONGBLOB\n\nA BLOB column with a maximum length of 4,294,967,295 or 4GB (232 - 1)\nbytes. The maximum effective (permitted) length of LONGBLOB columns\ndepends on the configured maximum packet size in the client/server\nprotocol and available memory.\n','','string-type-overview'),(256,'POINTN',11,'PointN(ls,N)\n\nReturns the N-th Point in the Linestring value ls. Points are numbered\nbeginning with 1.\n','mysql> SET @ls = \'LineString(1 1,2 2,3 3)\';\nmysql> SELECT AsText(PointN(GeomFromText(@ls),2));\n+-------------------------------------+\n| AsText(PointN(GeomFromText(@ls),2)) |\n+-------------------------------------+\n| POINT(2 2)                          |\n+-------------------------------------+\n','linestring-property-functions'),(257,'YEAR DATA TYPE',20,'YEAR[(2|4)]\n\nA year in two-digit or four-digit format. The default is four-digit\nformat. In four-digit format, the allowable values are 1901 to 2155,\nand 0000. In two-digit format, the allowable values are 70 to 69,\nrepresenting years from 1970 to 2069. MySQL displays YEAR values in\nYYYY format, but allows you to assign values to YEAR columns using\neither strings or numbers.\n','','date-and-time-type-overview'),(258,'SUM',14,'Syntax:\nSUM([DISTINCT] expr)\n\nReturns the sum of expr. If the return set has no rows, SUM() returns\nNULL. The DISTINCT keyword can be used in MySQL 5.0 to sum only the\ndistinct values of expr.\n\nSUM() returns NULL if there were no matching rows.\n','','group-by-functions'),(259,'OCT',33,'Syntax:\nOCT(N)\n\nReturns a string representation of the octal value of N, where N is a\nlonglong (BIGINT) number. This is equivalent to CONV(N,10,8). Returns\nNULL if N is NULL.\n','mysql> SELECT OCT(12);\n        -> \'14\'\n','string-functions'),(260,'SYSDATE',28,'Syntax:\nSYSDATE()\n\nReturns the current date and time as a value in \'YYYY-MM-DD HH:MM:SS\'\nor YYYYMMDDHHMMSS format, depending on whether the function is used in\na string or numeric context.\n\nWithin a stored routine or trigger, SYSDATE() returns the time at which\nit executes. This differs from the behavior for NOW(), which returns\nthe the time at which the routine or triggering statement began to\nexecute.\n','','date-and-time-functions'),(261,'ASBINARY',29,'AsBinary(g)\n\nConverts a value in internal geometry format to its WKB representation\nand returns the binary result.\n','SELECT AsBinary(g) FROM geom;\n','functions-to-convert-geometries-between-formats'),(262,'REPEAT FUNCTION',33,'Syntax:\nREPEAT(str,count)\n\nReturns a string consisting of the string str repeated count times. If\ncount is less than 1, returns an empty string. Returns NULL if str or\ncount are NULL.\n','mysql> SELECT REPEAT(\'MySQL\', 3);\n        -> \'MySQLMySQLMySQL\'\n','string-functions'),(263,'SHOW TABLES',25,'Syntax:\nSHOW [FULL] TABLES [FROM db_name] [LIKE \'pattern\']\n\nSHOW TABLES lists the non-TEMPORARY tables in a given database. You can\nalso get this list using the mysqlshow db_name command.\n\nBefore MySQL 5.0.1, the output from SHOW TABLES contains a single\ncolumn of table names. Beginning with MySQL 5.0.1, this statement also\nlists any views in the database. As of MySQL 5.0.2, the FULL modifier\nis supported such that SHOW FULL TABLES displays a second output\ncolumn. Values for the second column are BASE TABLE for a table and\nVIEW for a view.\n\nNote: If you have no privileges for a table, the table does not show up\nin the output from SHOW TABLES or mysqlshow db_name.\n','','show-tables'),(264,'MAKEDATE',28,'Syntax:\nMAKEDATE(year,dayofyear)\n\nReturns a date, given year and day-of-year values. dayofyear must be\ngreater than 0 or the result is NULL.\n','mysql> SELECT MAKEDATE(2001,31), MAKEDATE(2001,32);\n        -> \'2001-01-31\', \'2001-02-01\'\nmysql> SELECT MAKEDATE(2001,365), MAKEDATE(2004,365);\n        -> \'2001-12-31\', \'2004-12-30\'\nmysql> SELECT MAKEDATE(2001,0);\n        -> NULL\n','date-and-time-functions'),(265,'BINARY OPERATOR',33,'Syntax:\nBINARY\n\nThe BINARY operator casts the string following it to a binary string.\nThis is an easy way to force a column comparison to be done byte by\nbyte rather than character by character. This causes the comparison to\nbe case sensitive even if the column isn\'t defined as BINARY or BLOB.\nBINARY also causes trailing spaces to be significant.\n','mysql> SELECT \'a\' = \'A\';\n        -> 1\nmysql> SELECT BINARY \'a\' = \'A\';\n        -> 0\nmysql> SELECT \'a\' = \'a \';\n        -> 1\nmysql> SELECT BINARY \'a\' = \'a \';\n        -> 0\n','cast-functions'),(266,'MBROVERLAPS',5,'MBROverlaps(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangles of\nthe two geometries g1 and g2 overlap.\n','','relations-on-geometry-mbr'),(267,'SOUNDEX',33,'Syntax:\nSOUNDEX(str)\n\nReturns a soundex string from str. Two strings that sound almost the\nsame should have identical soundex strings. A standard soundex string\nis four characters long, but the SOUNDEX() function returns an\narbitrarily long string. You can use SUBSTRING() on the result to get a\nstandard soundex string. All non-alphabetic characters in str are\nignored. All international alphabetic characters outside the A-Z range\nare treated as vowels.\n','mysql> SELECT SOUNDEX(\'Hello\');\n        -> \'H400\'\nmysql> SELECT SOUNDEX(\'Quadratically\');\n        -> \'Q36324\'\n','string-functions'),(268,'SHOW MASTER LOGS',25,'Syntax:\nSHOW MASTER LOGS\nSHOW BINARY LOGS\n\nLists the binary log files on the server. This statement is used as\npart of the procedure described in [purge-master-logs], that shows how\nto determine which logs can be purged.\n\nmysql> SHOW BINARY LOGS;\n+---------------+-----------+\n| Log_name      | File_size |\n+---------------+-----------+\n| binlog.000015 |    724935 |\n| binlog.000016 |    733481 |\n+---------------+-----------+\n','','show-master-logs'),(269,'MBRTOUCHES',5,'MBRTouches(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangles of\nthe two geometries g1 and g2 touch.\n','','relations-on-geometry-mbr'),(270,'CREATE PROCEDURE',35,'Syntax:\nCREATE\n    [DEFINER = { user | CURRENT_USER }]\n    PROCEDURE sp_name ([proc_parameter[,...]])\n    [characteristic ...] routine_body\n\nCREATE\n    [DEFINER = { user | CURRENT_USER }]\n    FUNCTION sp_name ([func_parameter[,...]])\n    RETURNS type\n    [characteristic ...] routine_body\n    \nproc_parameter:\n    [ IN | OUT | INOUT ] param_name type\n    \nfunc_parameter:\n    param_name type\n\ntype:\n    Any valid MySQL data type\n\ncharacteristic:\n    LANGUAGE SQL\n  | [NOT] DETERMINISTIC\n  | { CONTAINS SQL | NO SQL | READS SQL DATA | MODIFIES SQL DATA }\n  | SQL SECURITY { DEFINER | INVOKER }\n  | COMMENT \'string\'\n\nroutine_body:\n    Valid SQL procedure statement\n\nThese statements create stored routines. As of MySQL 5.0.3, to use\nthem, it is necessary to have the CREATE ROUTINE privilege. If binary\nlogging is enabled, these statements might may also require the SUPER\nprivilege, as described in [stored-procedure-logging]. MySQL\nautomatically grants the ALTER ROUTINE and EXECUTE privileges to the\nroutine creator.\n\nBy default, the routine is associated with the default database. To\nassociate the routine explicitly with a given database, specify the\nname as db_name.sp_name when you create it.\n\nIf the routine name is the same as the name of a built-in SQL function,\nyou must use a space between the name and the following parenthesis\nwhen defining the routine, or a syntax error occurs. This is also true\nwhen you invoke the routine later. For this reason, we suggest that it\nis better to avoid re-using the names of existing SQL functions for\nyour own stored routines.\n\nThe IGNORE_SPACE SQL mode applies to built-in functions, not to stored\nroutines. it is always allowable to have spaces after a routine name,\nregardless of whether IGNORE_SPACE is enabled.\n\nThe parameter list enclosed within parentheses must always be present.\nIf there are no parameters, an empty parameter list of () should be\nused. Each parameter is an IN parameter by default. To specify\notherwise for a parameter, use the keyword OUT or INOUT before the\nparameter name.\n\nNote: Specifying a parameter as IN, OUT, or INOUT is valid only for a\nPROCEDURE. (FUNCTION parameters are always regarded as IN parameters.)\n\nEach parameter can be declared to use any valid data type, except that\nthe COLLATE attribute cannot be used.\n\nThe RETURNS clause may be specified only for a FUNCTION, for which it\nis mandatory. It indicates the return type of the function, and the\nfunction body must contain a RETURN value statement.\n\nThe routine_body consists of a valid SQL procedure statement. This can\nbe a simple statement such as SELECT or INSERT, or it can be a compound\nstatement written using BEGIN and END. Compound statement syntax is\ndescribed in [begin-end]. Compound statements can contain declarations,\nloops, and other control structure statements. The syntax for these\nstatements is described later in this chapter. See, for example,\n[declare], and [flow-control-constructs]. Some statements are not\nallowed in stored routines; see [routine-restrictions].\n','mysql> delimiter //\n\nmysql> CREATE PROCEDURE simpleproc (OUT param1 INT)\n    -> BEGIN\n    ->   SELECT COUNT(*) INTO param1 FROM t;\n    -> END;\n    -> //\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> delimiter ;\n\nmysql> CALL simpleproc(@a);\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> SELECT @a;\n+------+\n| @a   |\n+------+\n| 3    |\n+------+\n1 row in set (0.00 sec)\n','create-procedure'),(271,'INSERT SELECT',25,'Syntax:\nINSERT [LOW_PRIORITY | HIGH_PRIORITY] [IGNORE]\n    [INTO] tbl_name [(col_name,...)]\n    SELECT ...\n    [ ON DUPLICATE KEY UPDATE col_name=expr, ... ]\n\nWith INSERT ... SELECT, you can quickly insert many rows into a table\nfrom one or many tables. For example:\n\nINSERT INTO tbl_temp2 (fld_id)\n  SELECT tbl_temp1.fld_order_id\n  FROM tbl_temp1 WHERE tbl_temp1.fld_order_id > 100;\n','','insert-select'),(272,'VARBINARY',20,'VARBINARY(M)\n\nThe VARBINARY type is similar to the VARCHAR type, but stores binary\nbyte strings rather than non-binary character strings.\n','','string-type-overview'),(273,'LOAD INDEX',25,'Syntax:\nLOAD INDEX INTO CACHE\n  tbl_index_list [, tbl_index_list] ...\n\ntbl_index_list:\n  tbl_name\n    [[INDEX|KEY] (index_name[, index_name] ...)]\n    [IGNORE LEAVES]\n\nThe LOAD INDEX INTO CACHE statement preloads a table index into the key\ncache to which it has been assigned by an explicit CACHE INDEX\nstatement, or into the default key cache otherwise. LOAD INDEX INTO\nCACHE is used only for MyISAM tables.\n\nThe IGNORE LEAVES modifier causes only blocks for the non-leaf nodes of\nthe index to be preloaded.\n','','load-index'),(274,'UNION',25,'Syntax:\nSELECT ...\nUNION [ALL | DISTINCT] SELECT ...\n[UNION [ALL | DISTINCT] SELECT ...]\n\nUNION is used to combine the result from multiple SELECT statements\ninto a single result set.\n\nThe column names from the first SELECT statement are used as the column\nnames for the results returned. Selected columns listed in\ncorresponding positions of each SELECT statement should have the same\ndata type. (For example, the first column selected by the first\nstatement should have the same type as the first column selected by the\nother statements.)\n','','union'),(275,'TO_DAYS',28,'Syntax:\nTO_DAYS(date)\n\nGiven a date date, returns a day number (the number of days since year\n0).\n','mysql> SELECT TO_DAYS(950501);\n        -> 728779\nmysql> SELECT TO_DAYS(\'1997-10-07\');\n        -> 729669\n','date-and-time-functions'),(276,'NOT REGEXP',33,'Syntax:\nexpr NOT REGEXP pat, expr NOT RLIKE pat\n\nThis is the same as NOT (expr REGEXP pat).\n','','string-comparison-functions'),(277,'SHOW INDEX',25,'Syntax:\nSHOW INDEX FROM tbl_name [FROM db_name]\n\nSHOW INDEX returns table index information. The format resembles that\nof the SQLStatistics call in ODBC.\nYou can use db_name.tbl_name as an alternative to the tbl_name FROM\ndb_name syntax. These two statements are equivalent:\n\nSHOW INDEX FROM mytable FROM mydb;\nSHOW INDEX FROM mydb.mytable;\n\nSHOW KEYS is a synonym for SHOW INDEX. You can also list a table\'s\nindexes with the mysqlshow -k db_name tbl_name command.\n','','show-index'),(278,'SHOW CREATE DATABASE',25,'Syntax:\nSHOW CREATE {DATABASE | SCHEMA} db_name\n\nShows the CREATE DATABASE statement that creates the given database.\nSHOW CREATE SCHEMA is a synonym for SHOW CREATE DATABASE as of MySQL\n5.0.2.\n','mysql> SHOW CREATE DATABASE test\\G\n*************************** 1. row ***************************\n       Database: test\nCreate Database: CREATE DATABASE `test`\n                 /*!40100 DEFAULT CHARACTER SET latin1 */\n\nmysql> SHOW CREATE SCHEMA test\\G\n*************************** 1. row ***************************\n       Database: test\nCreate Database: CREATE DATABASE `test`\n                 /*!40100 DEFAULT CHARACTER SET latin1 */\n','show-create-database'),(279,'LEAVE',35,'Syntax:\nLEAVE label\n\nThis statement is used to exit any labeled flow control construct. It\ncan be used within BEGIN ... END or loop constructs (LOOP, REPEAT,\nWHILE).\n','','leave-statement'),(280,'NOT IN',17,'Syntax:\nexpr NOT IN (value,...)\n\nThis is the same as NOT (expr IN (value,...)).\n','','comparison-operators'),(281,'!',12,'Syntax:\nNOT, !\n\nLogical NOT. Evaluates to 1 if the operand is 0, to 0 if the operand is\nnon-zero, and NOT NULL returns NULL.\n','mysql> SELECT NOT 10;\n        -> 0\nmysql> SELECT NOT 0;\n        -> 1\nmysql> SELECT NOT NULL;\n        -> NULL\nmysql> SELECT ! (1+1);\n        -> 0\nmysql> SELECT ! 1+1;\n        -> 1\n','logical-operators'),(282,'DECLARE HANDLER',35,'Syntax:\nDECLARE handler_type HANDLER FOR condition_value[,...] statement\n\nhandler_type:\n    CONTINUE\n  | EXIT\n  | UNDO\n\ncondition_value:\n    SQLSTATE [VALUE] sqlstate_value\n  | condition_name\n  | SQLWARNING\n  | NOT FOUND\n  | SQLEXCEPTION\n  | mysql_error_code\n\nThe DECLARE ... HANDLER statement specifies handlers that each may deal\nwith one or more conditions. If one of these conditions occurs, the\nspecified statement is executed. statement can be a simple statement\n(for example, SET var_name = value), or it can be a compound statement\nwritten using BEGIN and END (see [begin-end]).\n\nFor a CONTINUE handler, execution of the current routine continues\nafter execution of the handler statement. For an EXIT handler,\nexecution terminates for the BEGIN ... END compound statement in which\nthe handler is declared. (This is true even if the condition occurs in\nan inner block.) The UNDO handler type statement is not yet supported.\n\nIf a condition occurs for which no handler has been declared, the\ndefault action is EXIT.\n\nA condition_value can be any of the following values:\n\no An SQLSTATE value or a MySQL error code.\n\no A condition name previously specified with DECLARE ... CONDITION. See\n  [declare-conditions].\n\no SQLWARNING is shorthand for all SQLSTATE codes that begin with 01.\n\no NOT FOUND is shorthand for all SQLSTATE codes that begin with 02.\n\no SQLEXCEPTION is shorthand for all SQLSTATE codes not caught by\n  SQLWARNING or NOT FOUND.\n','mysql> CREATE TABLE test.t (s1 int,primary key (s1));\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> delimiter //\n\nmysql> CREATE PROCEDURE handlerdemo ()\n    -> BEGIN\n    ->   DECLARE CONTINUE HANDLER FOR SQLSTATE \'23000\' SET @x2 = 1;\n    ->   SET @x = 1;\n    ->   INSERT INTO test.t VALUES (1);\n    ->   SET @x = 2;\n    ->   INSERT INTO test.t VALUES (1);\n    ->   SET @x = 3;\n    -> END;\n    -> //\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> CALL handlerdemo()//\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> SELECT @x//\n    +------+\n    | @x   |\n    +------+\n    | 3    |\n    +------+\n    1 row in set (0.00 sec)\n','declare-handlers'),(283,'DOUBLE',20,'DOUBLE[(M,D)] [UNSIGNED] [ZEROFILL]\n\nA normal-size (double-precision) floating-point number. Allowable\nvalues are -1.7976931348623157E+308 to -2.2250738585072014E-308, 0, and\n2.2250738585072014E-308 to 1.7976931348623157E+308. These are the\ntheoretical limits, based on the IEEE standard. The actual range might\nbe slightly smaller depending on your hardware or operating system.\n\nM is the total number of decimal digits and D is the number of digits\nfollowing the decimal point. If M and D are omitted, values are stored\nto the limits allowed by the hardware. A double-precision\nfloating-point number is accurate to approximately 15 decimal places.\n\nUNSIGNED, if specified, disallows negative values.\n','','numeric-type-overview'),(284,'TIME',20,'TIME\n\nA time. The range is \'-838:59:59\' to \'838:59:59\'. MySQL displays TIME\nvalues in \'HH:MM:SS\' format, but allows you to assign values to TIME\ncolumns using either strings or numbers.\n','','date-and-time-type-overview'),(285,'&&',12,'Syntax:\nAND, &&\n\nLogical AND. Evaluates to 1 if all operands are non-zero and not NULL,\nto 0 if one or more operands are 0, otherwise NULL is returned.\n','mysql> SELECT 1 && 1;\n        -> 1\nmysql> SELECT 1 && 0;\n        -> 0\nmysql> SELECT 1 && NULL;\n        -> NULL\nmysql> SELECT 0 && NULL;\n        -> 0\nmysql> SELECT NULL && 0;\n        -> 0\n','logical-operators'),(286,'X',9,'X(p)\n\nReturns the X-coordinate value for the point p as a double-precision\nnumber.\n','mysql> SET @pt = \'Point(56.7 53.34)\';\nmysql> SELECT X(GeomFromText(@pt));\n+----------------------+\n| X(GeomFromText(@pt)) |\n+----------------------+\n|                 56.7 |\n+----------------------+\n','point-property-functions'),(287,'FOUND_ROWS',15,'Syntax:\nFOUND_ROWS()\n\nA SELECT statement may include a LIMIT clause to restrict the number of\nrows the server returns to the client. In some cases, it is desirable\nto know how many rows the statement would have returned without the\nLIMIT, but without running the statement again. To obtain this row\ncount, include a SQL_CALC_FOUND_ROWS option in the SELECT statement,\nand then invoke FOUND_ROWS() afterward:\n','mysql> SELECT SQL_CALC_FOUND_ROWS * FROM tbl_name\n    -> WHERE id > 100 LIMIT 10;\nmysql> SELECT FOUND_ROWS();\n','information-functions'),(288,'SYSTEM_USER',15,'Syntax:\nSYSTEM_USER()\n\nSYSTEM_USER() is a synonym for USER().\n','','information-functions'),(289,'CROSSES',26,'Crosses(g1,g2)\n\nReturns 1 if g1 spatially crosses g2. Returns NULL if g1 is a Polygon\nor a MultiPolygon, or if g2 is a Point or a MultiPoint. Otherwise,\nreturns 0.\n\nThe term spatially crosses denotes a spatial relation between two given\ngeometries that has the following properties:\n\no The two geometries intersect\n\no Their intersection results in a geometry that has a dimension that is\n  one less than the maximum dimension of the two given geometries\n\no Their intersection is not equal to either of the two given geometries\n','','functions-that-test-spatial-relationships-between-geometries'),(290,'TRUNCATE TABLE',25,'Syntax:\nTRUNCATE [TABLE] tbl_name\n\nTRUNCATE TABLE empties a table completely. Logically, this is\nequivalent to a DELETE statement that deletes all rows, but there are\npractical differences under some circumstances.\n\nFor InnoDB before version 5.0.3, TRUNCATE TABLE is mapped to DELETE, so\nthere is no difference. Starting with MySQL 5.0.3, fast TRUNCATE TABLE\nis available. However, the operation is still mapped to DELETE if there\nare foreign key constraints that reference the table. (When fast\ntruncate is used, it resets any AUTO_INCREMENT counter. From MySQL\n5.0.13 on, the AUTO_INCREMENT counter is reset by TRUNCATE TABLE,\nregardless of whether there is a foreign key constraint.)\n\nFor other storage engines, TRUNCATE TABLE differs from DELETE in the\nfollowing ways in MySQL 5.0:\n\no Truncate operations drop and re-create the table, which is much\n  faster than deleting rows one by one.\n\no Truncate operations are not transaction-safe; an error occurs when\n  attempting one in the course of an active transaction or active table\n  lock.\n\no The number of deleted rows is not returned.\n\no As long as the table format file tbl_name.frm is valid, the table can\n  be re-created as an empty table with TRUNCATE TABLE, even if the data\n  or index files have become corrupted.\n\no The table handler does not remember the last used AUTO_INCREMENT\n  value, but starts counting from the beginning. This is true even for\n  MyISAM and InnoDB, which normally do not reuse sequence values.\n\nSince truncation of a table does not make any use of DELETE, the\nTRUNCATE statement does not invoke ON DELETE triggers.\n\nTRUNCATE TABLE is an Oracle SQL extension adopted in MySQL.\n','','truncate'),(291,'BIT_XOR',14,'Syntax:\nBIT_XOR(expr)\n\nReturns the bitwise XOR of all bits in expr. The calculation is\nperformed with 64-bit (BIGINT) precision.\n','','group-by-functions'),(292,'CURRENT_DATE',28,'Syntax:\nCURRENT_DATE, CURRENT_DATE()\n\nCURRENT_DATE and CURRENT_DATE() are synonyms for CURDATE().\n','','date-and-time-functions'),(293,'AREA',2,'Area(poly)\n\nReturns as a double-precision number the area of the Polygon value\npoly, as measured in its spatial reference system.\n','mysql> SET @poly = \'Polygon((0 0,0 3,3 0,0 0),(1 1,1 2,2 1,1 1))\';\nmysql> SELECT Area(GeomFromText(@poly));\n+---------------------------+\n| Area(GeomFromText(@poly)) |\n+---------------------------+\n|                         4 |\n+---------------------------+\n','polygon-property-functions'),(294,'START SLAVE',25,'Syntax:\nSTART SLAVE [thread_type [, thread_type] ... ]\nSTART SLAVE [SQL_THREAD] UNTIL\n    MASTER_LOG_FILE = \'log_name\', MASTER_LOG_POS = log_pos\nSTART SLAVE [SQL_THREAD] UNTIL\n    RELAY_LOG_FILE = \'log_name\', RELAY_LOG_POS = log_pos\n\nthread_type: IO_THREAD | SQL_THREAD\n\nSTART SLAVE with no thread_type options starts both of the slave\nthreads. The I/O thread reads queries from the master server and stores\nthem in the relay log. The SQL thread reads the relay log and executes\nthe queries. START SLAVE requires the SUPER privilege.\n\nIf START SLAVE succeeds in starting the slave threads, it returns\nwithout any error. However, even in that case, it might be that the\nslave threads start and then later stop (for example, because they do\nnot manage to connect to the master or read its binary logs, or some\nother problem). START SLAVE does not warn you about this. You must\ncheck the slave\'s error log for error messages generated by the slave\nthreads, or check that they are running satisfactorily with SHOW SLAVE\nSTATUS.\n','','start-slave'),(295,'BEGIN END',35,'Syntax:\n[begin_label:] BEGIN\n    [statement_list]\nEND [end_label]\n\nBEGIN ... END syntax is used for writing compound statements, which can\nappear within stored routines and triggers. A compound statement can\ncontain multiple statements, enclosed by the BEGIN and END keywords.\nstatement_list represents a list of one or more statements. Each\nstatement within statement_list must be terminated by a semicolon (;)\nstatement delimiter. Note that statement_list is optional, which means\nthat the empty compound statement (BEGIN END) is legal.\n\nUse of multiple statements requires that a client is able to send\nstatement strings containing the ; statement delimiter. This is handled\nin the mysql command-line client with the delimiter command. Changing\nthe ; end-of-statement delimiter (for example, to //) allows ; to be\nused in a routine body. For an example, see [create-procedure].\n\nA compound statement can be labeled. end_label cannot be given unless\nbegin_label also is present. If both are present, they must be the\nsame.\n','','begin-end'),(296,'FLUSH',25,'Syntax:\nFLUSH [LOCAL | NO_WRITE_TO_BINLOG] flush_option [, flush_option] ...\n\nThe FLUSH statement clears or reloads various internal caches used by\nMySQL. To execute FLUSH, you must have the RELOAD privilege.\n\nThe RESET statement is similar to FLUSH. See [reset].\n','','flush'),(297,'SHOW PROCEDURE STATUS',25,'Syntax:\nSHOW {PROCEDURE | FUNCTION} STATUS [LIKE \'pattern\']\n\nThis statement is a MySQL extension. It returns characteristics of\nroutines, such as the database, name, type, creator, and creation and\nmodification dates. If no pattern is specified, the information for all\nstored procedures or all stored functions is listed, depending on which\nstatement you use.\n','mysql> SHOW FUNCTION STATUS LIKE \'hello\'\\G\n*************************** 1. row ***************************\n           Db: test\n         Name: hello\n         Type: FUNCTION\n      Definer: testuser@localhost\n     Modified: 2004-08-03 15:29:37\n      Created: 2004-08-03 15:29:37\nSecurity_type: DEFINER\n      Comment:\n','show-procedure-status'),(298,'SHOW WARNINGS',25,'Syntax:\nSHOW WARNINGS [LIMIT [offset,] row_count]\nSHOW COUNT(*) WARNINGS\n\nSHOW WARNINGS shows the error, warning, and note messages that resulted\nfrom the last statement that generated messages, or nothing if the last\nstatement that used a table generated no messages. A related statement,\nSHOW ERRORS, shows only the errors. See [show-errors].\n\nThe list of messages is reset for each new statement that uses a table.\n\nThe SHOW COUNT(*) WARNINGS statement displays the total number of\nerrors, warnings, and notes. You can also retrieve this number from the\nwarning_count variable:\n\nSHOW COUNT(*) WARNINGS;\nSELECT @@warning_count;\n\nThe value of warning_count might be greater than the number of messages\ndisplayed by SHOW WARNINGS if the max_error_count system variable is\nset so low that not all messages are stored. An example shown later in\nthis section demonstrates how this can happen.\n\nThe LIMIT clause has the same syntax as for the SELECT statement. See\n[select].\n','','show-warnings'),(299,'DESCRIBE',24,'Syntax:\n{DESCRIBE | DESC} tbl_name [col_name | wild]\n\nDESCRIBE provides information about the columns in a table. It is a\nshortcut for SHOW COLUMNS FROM. As of MySQL 5.0.1, these statements\nalso display information for views. (See [show-columns].)\n','','describe'),(300,'DROP USER',8,'Syntax:\nDROP USER user [, user] ...\n\nThe DROP USER statement removes one or more MySQL accounts. To use it,\nyou must have the global CREATE USER privilege or the DELETE privilege\nfor the mysql database. Each account is named using the same format as\nfor the GRANT statement; for example, \'jeffrey\'@\'localhost\'. The user\nand host parts of the account name correspond to the User and Host\ncolumn values of the user table row for the account.\n\nDROP USER as present in MySQL 5.0.0 removes only accounts that have no\nprivileges. In MySQL 5.0.2, it was modified to remove account\nprivileges as well. This means that the procedure for removing an\naccount depends on your version of MySQL.\n\nAs of MySQL 5.0.2, you can remove an account and its privileges as\nfollows:\n\nDROP USER user;\n\nThe statement removes privilege rows for the account from all grant\ntables.\n','','drop-user'),(301,'STDDEV_POP',14,'Syntax:\nSTDDEV_POP(expr)\n\nReturns the population standard deviation of expr (the square root of\nVAR_POP()). This function was added in MySQL 5.0.3. Before 5.0.3, you\ncan use STD() or STDDEV(), which are equivalent but not standard SQL.\n\nSTDDEV_POP() returns NULL if there were no matching rows.\n','','group-by-functions'),(302,'SHOW CHARACTER SET',25,'Syntax:\nSHOW CHARACTER SET [LIKE \'pattern\']\n\nThe SHOW CHARACTER SET statement shows all available character sets. It\ntakes an optional LIKE clause that indicates which character set names\nto match. For example:\n\nmysql> SHOW CHARACTER SET LIKE \'latin%\';\n+---------+-----------------------------+-------------------+--------+\n| Charset | Description                 | Default collation | Maxlen |\n+---------+-----------------------------+-------------------+--------+\n| latin1  | cp1252 West European        | latin1_swedish_ci |      1 |\n| latin2  | ISO 8859-2 Central European | latin2_general_ci |      1 |\n| latin5  | ISO 8859-9 Turkish          | latin5_turkish_ci |      1 |\n| latin7  | ISO 8859-13 Baltic          | latin7_general_ci |      1 |\n+---------+-----------------------------+-------------------+--------+\n','','show-character-set'),(303,'SUBSTRING',33,'Syntax:\nSUBSTRING(str,pos), SUBSTRING(str FROM pos), SUBSTRING(str,pos,len),\nSUBSTRING(str FROM pos FOR len)\n\nThe forms without a len argument return a substring from string str\nstarting at position pos. The forms with a len argument return a\nsubstring len characters long from string str, starting at position\npos. The forms that use FROM are standard SQL syntax. It is also\npossible to use a negative value for pos. In this case, the beginning\nof the substring is pos characters from the end of the string, rather\nthan the beginning. A negative value may be used for pos in any of the\nforms of this function.\n','mysql> SELECT SUBSTRING(\'Quadratically\',5);\n        -> \'ratically\'\nmysql> SELECT SUBSTRING(\'foobarbar\' FROM 4);\n        -> \'barbar\'\nmysql> SELECT SUBSTRING(\'Quadratically\',5,6);\n        -> \'ratica\'        \nmysql> SELECT SUBSTRING(\'Sakila\', -3);\n        -> \'ila\'        \nmysql> SELECT SUBSTRING(\'Sakila\', -5, 3);\n        -> \'aki\'\nmysql> SELECT SUBSTRING(\'Sakila\' FROM -4 FOR 2);\n        -> \'ki\'\n','string-functions'),(304,'ISEMPTY',32,'IsEmpty(g)\n\nReturns 1 if the geometry value g is the empty geometry, 0 if it is not\nempty, and -1 if the argument is NULL. If the geometry is empty, it\nrepresents the empty point set.\n','','general-geometry-property-functions'),(305,'LTRIM',33,'Syntax:\nLTRIM(str)\n\nReturns the string str with leading space characters removed.\n','mysql> SELECT LTRIM(\'  barbar\');\n        -> \'barbar\'\n','string-functions'),(306,'INTERSECTS',26,'Intersects(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 spatially intersects g2.\n','','functions-that-test-spatial-relationships-between-geometries'),(307,'CALL',35,'Syntax:\nCALL sp_name([parameter[,...]])\n\nThe CALL statement invokes a procedure that was defined previously with\nCREATE PROCEDURE.\n\nCALL can pass back values to its caller using parameters that are\ndeclared as OUT or INOUT parameters. It also \"returns\" the number of\nrows affected, which a client program can obtain at the SQL level by\ncalling the ROW_COUNT() function and from C by calling the\nmysql_affected_rows() C API function.\n','','call'),(308,'MBRDISJOINT',5,'MBRDisjoint(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangles of\nthe two geometries g1 and g2 are disjoint (do not intersect).\n','','relations-on-geometry-mbr'),(309,'VALUES',13,'Syntax:\nVALUES(col_name)\n\nIn an INSERT ... ON DUPLICATE KEY UPDATE statement, you can use the\nVALUES(col_name) function in the UPDATE clause to refer to column\nvalues from the INSERT portion of the statement. In other words,\nVALUES(col_name) in the UPDATE clause refers to the value of col_name\nthat would be inserted, had no duplicate-key conflict occurred. This\nfunction is especially useful in multiple-row inserts. The VALUES()\nfunction is meaningful only in INSERT ... ON DUPLICATE KEY UPDATE\nstatements and returns NULL otherwise. [insert-on-duplicate].\n','mysql> INSERT INTO table (a,b,c) VALUES (1,2,3),(4,5,6)\n    -> ON DUPLICATE KEY UPDATE c=VALUES(a)+VALUES(b);\n','miscellaneous-functions'),(310,'SUBSTRING_INDEX',33,'Syntax:\nSUBSTRING_INDEX(str,delim,count)\n\nReturns the substring from string str before count occurrences of the\ndelimiter delim. If count is positive, everything to the left of the\nfinal delimiter (counting from the left) is returned. If count is\nnegative, everything to the right of the final delimiter (counting from\nthe right) is returned. SUBSTRING_INDEX() performs a case-sensitive\nmatch when searching for delim.\n','mysql> SELECT SUBSTRING_INDEX(\'www.mysql.com\', \'.\', 2);\n        -> \'www.mysql\'\nmysql> SELECT SUBSTRING_INDEX(\'www.mysql.com\', \'.\', -2);\n        -> \'mysql.com\'\n','string-functions'),(311,'ENCODE',10,'Syntax:\nENCODE(str,pass_str)\n\nEncrypt str using pass_str as the password. To decrypt the result, use\nDECODE().\n\nThe result is a binary string of the same length as str.\n','','encryption-functions'),(312,'LOOP',35,'Syntax:\n[begin_label:] LOOP\n    statement_list\nEND LOOP [end_label]\n\nLOOP implements a simple loop construct, enabling repeated execution of\nthe statement list, which consists of one or more statements. The\nstatements within the loop are repeated until the loop is exited;\nusually this is accomplished with a LEAVE statement.\n\nA LOOP statement can be labeled. end_label cannot be given unless\nbegin_label also is present. If both are present, they must be the\nsame.\n','','loop-statement'),(313,'TRUNCATE',4,'Syntax:\nTRUNCATE(X,D)\n\nReturns the number X, truncated to D decimal places. If D is 0, the\nresult has no decimal point or fractional part. D can be negative to\ncause D digits left of the decimal point of the value X to become zero.\n','mysql> SELECT TRUNCATE(1.223,1);\n        -> 1.2\nmysql> SELECT TRUNCATE(1.999,1);\n        -> 1.9\nmysql> SELECT TRUNCATE(1.999,0);\n        -> 1\nmysql> SELECT TRUNCATE(-1.999,1);\n        -> -1.9\nmysql> SELECT TRUNCATE(122,-2);\n       -> 100\nmysql> SELECT TRUNCATE(10.28*100,0);\n       -> 1028\n','mathematical-functions'),(314,'TIMESTAMPADD',28,'Syntax:\nTIMESTAMPADD(interval,int_expr,datetime_expr)\n\nAdds the integer expression int_expr to the date or datetime expression\ndatetime_expr. The unit for int_expr is given by the interval argument,\nwhich should be one of the following values: FRAC_SECOND, SECOND,\nMINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, or YEAR.\n\nThe interval value may be specified using one of keywords as shown, or\nwith a prefix of SQL_TSI_. For example, DAY and SQL_TSI_DAY both are\nlegal.\n','mysql> SELECT TIMESTAMPADD(MINUTE,1,\'2003-01-02\');\n        -> \'2003-01-02 00:01:00\'\nmysql> SELECT TIMESTAMPADD(WEEK,1,\'2003-01-02\');\n        -> \'2003-01-09\'\n','date-and-time-functions'),(315,'SHOW',25,'SHOW has many forms that provide information about databases, tables,\ncolumns, or status information about the server. This section describes\nthose following:\n\nSHOW [FULL] COLUMNS FROM tbl_name [FROM db_name] [LIKE \'pattern\']\nSHOW CREATE DATABASE db_name\nSHOW CREATE FUNCTION funcname\nSHOW CREATE PROCEDURE procname\nSHOW CREATE TABLE tbl_name\nSHOW DATABASES [LIKE \'pattern\']\nSHOW ENGINE engine_name {LOGS | STATUS }\nSHOW [STORAGE] ENGINES\nSHOW ERRORS [LIMIT [offset,] row_count]\nSHOW FUNCTION STATUS [LIKE \'pattern\']\nSHOW GRANTS FOR user\nSHOW INDEX FROM tbl_name [FROM db_name]\nSHOW INNODB STATUS\nSHOW PROCEDURE STATUS [LIKE \'pattern\']\nSHOW [BDB] LOGS\nSHOW PRIVILEGES\nSHOW [FULL] PROCESSLIST\nSHOW [GLOBAL | SESSION] STATUS [LIKE \'pattern\']\nSHOW TABLE STATUS [FROM db_name] [LIKE \'pattern\']\nSHOW [OPEN] TABLES [FROM db_name] [LIKE \'pattern\']\nSHOW TRIGGERS\nSHOW [GLOBAL | SESSION] VARIABLES [LIKE \'pattern\']\nSHOW WARNINGS [LIMIT [offset,] row_count]\n\nThe SHOW statement also has forms that provide information about\nreplication master and slave servers and are described in\n[replication-sql]:\n\nSHOW BINLOG EVENTS\nSHOW MASTER LOGS\nSHOW MASTER STATUS\nSHOW SLAVE HOSTS\nSHOW SLAVE STATUS\n\nIf the syntax for a given SHOW statement includes a LIKE \'pattern\'\npart, \'pattern\' is a string that can contain the SQL `%\' and `_\'\nwildcard characters. The pattern is useful for restricting statement\noutput to matching values.\n\nSeveral SHOW statements also accept a WHERE clause that provides more\nflexibility in specifying which rows to display. See [extended-show].\n','','show'),(316,'GREATEST',17,'Syntax:\nGREATEST(value1,value2,...)\n\nWith two or more arguments, returns the largest (maximum-valued)\nargument. The arguments are compared using the same rules as for\nLEAST().\n','mysql> SELECT GREATEST(2,0);\n        -> 2\nmysql> SELECT GREATEST(34.0,3.0,5.0,767.0);\n        -> 767.0\nmysql> SELECT GREATEST(\'B\',\'A\',\'C\');\n        -> \'C\'\n','comparison-operators'),(317,'OCTETLENGTH',33,'Syntax:\nOCTET_LENGTH(str)\n\nOCTET_LENGTH() is a synonym for LENGTH().\n','','string-functions'),(318,'SHOW VARIABLES',25,'Syntax:\nSHOW [GLOBAL | SESSION] VARIABLES [LIKE \'pattern\']\n\nSHOW VARIABLES shows the values of MySQL system variables. This\ninformation also can be obtained using the mysqladmin variables\ncommand.\n\nWith the GLOBAL modifier, SHOW VARIABLES displays the values that are\nused for new connections to MySQL. With SESSION, it displays the values\nthat are in effect for the current connection. If no modifier is\npresent, the default is SESSION. LOCAL is a synonym for SESSION.\nWith a LIKE clause, the statement displays only those variables that\nmatch the pattern. To obtain a specific variable name, use a LIKE\nclause as shown:\n\nSHOW VARIABLES LIKE \'max_join_size\';\nSHOW SESSION VARIABLES LIKE \'max_join_size\';\n\nTo get a list of variables whose name match a pattern, use the `%\'\nwildcard character in a LIKE clause:\n\nSHOW VARIABLES LIKE \'%size%\';\nSHOW GLOBAL VARIABLES LIKE \'%size%\';\n\nWildcard characters can be used in any position within the pattern to\nbe matched. Strictly speaking, because `_\' is a wildcard that matches\nany single character, you should escape it as `\\_\' to match it\nliterally. In practice, this is rarely necessary.\n','','show-variables'),(319,'BIT_AND',14,'Syntax:\nBIT_AND(expr)\n\nReturns the bitwise AND of all bits in expr. The calculation is\nperformed with 64-bit (BIGINT) precision.\n','','group-by-functions'),(320,'SECOND',28,'Syntax:\nSECOND(time)\n\nReturns the second for time, in the range 0 to 59.\n','mysql> SELECT SECOND(\'10:05:03\');\n        -> 3\n','date-and-time-functions'),(321,'ATAN2',4,'Syntax:\nATAN(Y,X), ATAN2(Y,X)\n\nReturns the arc tangent of the two variables X and Y. It is similar to\ncalculating the arc tangent of Y / X, except that the signs of both\narguments are used to determine the quadrant of the result.\n','mysql> SELECT ATAN(-2,2);\n        -> -0.78539816339745\nmysql> SELECT ATAN2(PI(),0);\n        -> 1.5707963267949\n','mathematical-functions'),(322,'MBRCONTAINS',5,'MBRContains(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangle of g1\ncontains the Minimum Bounding Rectangle of g2.\n','mysql> SET @g1 = GeomFromText(\'Polygon((0 0,0 3,3 3,3 0,0 0))\');\nmysql> SET @g2 = GeomFromText(\'Point(1 1)\');\nmysql> SELECT MBRContains(@g1,@g2), MBRContains(@g2,@g1);\n----------------------+----------------------+\n| MBRContains(@g1,@g2) | MBRContains(@g2,@g1) |\n+----------------------+----------------------+\n|                    1 |                    0 |\n+----------------------+----------------------+\n','relations-on-geometry-mbr'),(323,'HOUR',28,'Syntax:\nHOUR(time)\n\nReturns the hour for time. The range of the return value is 0 to 23 for\ntime-of-day values. However, the range of TIME values actually is much\nlarger, so HOUR can return values greater than 23.\n','mysql> SELECT HOUR(\'10:05:03\');\n        -> 10\nmysql> SELECT HOUR(\'272:59:59\');\n        -> 272\n','date-and-time-functions'),(324,'SELECT',25,'Syntax:\nSELECT\n    [ALL | DISTINCT | DISTINCTROW ]\n      [HIGH_PRIORITY]\n      [STRAIGHT_JOIN]\n      [SQL_SMALL_RESULT] [SQL_BIG_RESULT] [SQL_BUFFER_RESULT]\n      [SQL_CACHE | SQL_NO_CACHE] [SQL_CALC_FOUND_ROWS]\n    select_expr, ...\n    [FROM table_references\n    [WHERE where_condition]\n    [GROUP BY {col_name | expr | position}\n      [ASC | DESC], ... [WITH ROLLUP]]\n    [HAVING where_condition]\n    [ORDER BY {col_name | expr | position}\n      [ASC | DESC], ...]\n    [LIMIT {[offset,] row_count | row_count OFFSET offset}]\n    [PROCEDURE procedure_name(argument_list)]\n    [INTO OUTFILE \'file_name\' export_options\n      | INTO DUMPFILE \'file_name\']\n    [FOR UPDATE | LOCK IN SHARE MODE]]\n\nSELECT is used to retrieve rows selected from one or more tables, and\ncan include UNION statements and subqueries. See [union], and\n[subqueries].\n\nThe most commonly used clauses of SELECT statements are these:\n\no Each select_expr indicates a column that you want to retrieve. There\n  must be at least one select_expr.\n\no table_references indicates the table or tables from which to retrieve\n  rows. Its syntax is described in [join].\n\no The WHERE clause, if given, indicates the condition or conditions\n  that rows must satisfy to be selected. where_condition is an\n  expression that evaluates to true for each row to be selected. The\n  statement selects all rows if there is no WHERE clause.\n\n  In the WHERE clause, you can use any of the functions and operators\n  that MySQL supports, except for aggregate (summary) functions. See\n  [functions].\n\nSELECT can also be used to retrieve rows computed without reference to\nany table.\n','','select'),(325,'COT',4,'Syntax:\nCOT(X)\n\nReturns the cotangent of X.\n','mysql> SELECT COT(12);\n        -> -1.5726734063977\nmysql> SELECT COT(0);\n        -> NULL\n','mathematical-functions'),(326,'BACKUP TABLE',19,'Syntax:\nBACKUP TABLE tbl_name [, tbl_name] ... TO \'/path/to/backup/directory\'\n\nNote: This statement is deprecated. We are working on a better\nreplacement for it that will provide online backup capabilities. In the\nmeantime, the mysqlhotcopy script can be used instead.\n\nBACKUP TABLE copies to the backup directory the minimum number of table\nfiles needed to restore the table, after flushing any buffered changes\nto disk. The statement works only for MyISAM tables. It copies the .frm\ndefinition and .MYD data files. The .MYI index file can be rebuilt from\nthose two files. The directory should be specified as a full pathname.\nTo restore the table, use RESTORE TABLE.\n','','backup-table'),(327,'LOAD_FILE',33,'Syntax:\nLOAD_FILE(file_name)\n\nReads the file and returns the file contents as a string. To use this\nfunction, the file must be located on the server host, you must specify\nthe full pathname to the file, and you must have the FILE privilege.\nThe file must be readable by all and its size less than\nmax_allowed_packet bytes.\n\nIf the file does not exist or cannot be read because one of the\npreceding conditions is not satisfied, the function returns NULL.\n\nAs of MySQL 5.0.19, the character_set_filesystem system variable\ncontrols interpretation of filenames that are given as literal strings.\n','mysql> UPDATE t\n            SET blob_col=LOAD_FILE(\'/tmp/picture\')\n            WHERE id=1;\n','string-functions'),(328,'POINTFROMTEXT',3,'PointFromText(wkt[,srid])\n\nConstructs a POINT value using its WKT representation and SRID.\n','','gis-wkt-functions'),(329,'LOAD TABLE FROM MASTER',25,'Syntax:\nLOAD TABLE tbl_name FROM MASTER\n\nTransfers a copy of the table from the master to the slave. This\nstatement is implemented mainly debugging LOAD DATA FROM MASTER\noperations. To use LOAD TABLE, the account used for connecting to the\nmaster server must have the RELOAD and SUPER privileges on the master\nand the SELECT privilege for the master table to load. On the slave\nside, the user that issues LOAD TABLE FROM MASTER must have privileges\nfor dropping and creating the table.\n\nThe conditions for LOAD DATA FROM MASTER apply here as well. For\nexample, LOAD TABLE FROM MASTER works only for MyISAM tables. The\ntimeout notes for LOAD DATA FROM MASTER apply as well.\n','','load-table-from-master'),(330,'GROUP_CONCAT',14,'Syntax:\nGROUP_CONCAT(expr)\n\nThis function returns a string result with the concatenated non-NULL\nvalues from a group. It returns NULL if there are no non-NULL values.\nThe full syntax is as follows:\n\nGROUP_CONCAT([DISTINCT] expr [,expr ...]\n             [ORDER BY {unsigned_integer | col_name | expr}\n                 [ASC | DESC] [,col_name ...]]\n             [SEPARATOR str_val])\n','mysql> SELECT student_name,\n    ->     GROUP_CONCAT(test_score)\n    ->     FROM student\n    ->     GROUP BY student_name;\n','group-by-functions'),(331,'DATE_FORMAT',28,'Syntax:\nDATE_FORMAT(date,format)\n\nFormats the date value according to the format string.\n','mysql> SELECT DATE_FORMAT(\'1997-10-04 22:23:00\', \'%W %M %Y\');\n        -> \'Saturday October 1997\'\nmysql> SELECT DATE_FORMAT(\'1997-10-04 22:23:00\', \'%H:%i:%s\');\n        -> \'22:23:00\'\nmysql> SELECT DATE_FORMAT(\'1997-10-04 22:23:00\',\n                          \'%D %y %a %d %m %b %j\');\n        -> \'4th 97 Sat 04 10 Oct 277\'\nmysql> SELECT DATE_FORMAT(\'1997-10-04 22:23:00\',\n                          \'%H %k %I %r %T %S %w\');\n        -> \'22 22 10 10:23:00 PM 22:23:00 00 6\'\nmysql> SELECT DATE_FORMAT(\'1999-01-01\', \'%X %V\');\n        -> \'1998 52\'\nmysql> SELECT DATE_FORMAT(\'2006-06-00\', \'%d\');\n        -> \'00\'\n','date-and-time-functions'),(332,'BENCHMARK',15,'Syntax:\nBENCHMARK(count,expr)\n\nThe BENCHMARK() function executes the expression expr repeatedly count\ntimes. It may be used to time how quickly MySQL processes the\nexpression. The result value is always 0. The intended use is from\nwithin the mysql client, which reports query execution times:\n','mysql> SELECT BENCHMARK(1000000,ENCODE(\'hello\',\'goodbye\'));\n+----------------------------------------------+\n| BENCHMARK(1000000,ENCODE(\'hello\',\'goodbye\')) |\n+----------------------------------------------+\n|                                            0 |\n+----------------------------------------------+\n1 row in set (4.74 sec)\n','information-functions'),(333,'YEAR',28,'Syntax:\nYEAR(date)\n\nReturns the year for date, in the range 1000 to 9999, or 0 for the\n\"zero\" date.\n','mysql> SELECT YEAR(\'98-02-03\');\n        -> 1998\n','date-and-time-functions'),(334,'SHOW ENGINE',25,'Syntax:\nSHOW ENGINE engine_name {LOGS | STATUS }\n\nSHOW ENGINE displays log or status information about a storage engine.\nThe following statements currently are supported:\n\nSHOW ENGINE BDB LOGS\nSHOW ENGINE INNODB STATUS\n','','show-engine'),(335,'NAME_CONST',13,'Syntax:\nNAME_CONST(name,value)\n\nReturns the given value. When used to produce a result set column,\nNAME_CONST() causes the column to have the given name.\n\nmysql> SELECT NAME_CONST(\'myname\', 14);\n+--------+\n| myname |\n+--------+\n|     14 |\n+--------+\n','','miscellaneous-functions'),(336,'RELEASE_LOCK',13,'Syntax:\nRELEASE_LOCK(str)\n\nReleases the lock named by the string str that was obtained with\nGET_LOCK(). Returns 1 if the lock was released, 0 if the lock was not\nestablished by this thread (in which case the lock is not released),\nand NULL if the named lock did not exist. The lock does not exist if it\nwas never obtained by a call to GET_LOCK() or if it has previously been\nreleased.\n\nThe DO statement is convenient to use with RELEASE_LOCK(). See [do].\n','','miscellaneous-functions'),(337,'IS NULL',17,'Syntax:\nIS NULL, IS NOT NULL\n\nTests whether a value is or is not NULL.\n','mysql> SELECT 1 IS NULL, 0 IS NULL, NULL IS NULL;\n        -> 0, 0, 1\nmysql> SELECT 1 IS NOT NULL, 0 IS NOT NULL, NULL IS NOT NULL;\n        -> 1, 1, 0\n','comparison-operators'),(338,'CONVERT_TZ',28,'Syntax:\nCONVERT_TZ(dt,from_tz,to_tz)\n\nCONVERT_TZ() converts a datetime value dt from the time zone given by\nfrom_tz to the time zone given by to_tz and returns the resulting\nvalue. Time zones are specified as described in [time-zone-support].\nThis function returns NULL if the arguments are invalid.\n','mysql> SELECT CONVERT_TZ(\'2004-01-01 12:00:00\',\'GMT\',\'MET\');\n        -> \'2004-01-01 13:00:00\'\nmysql> SELECT CONVERT_TZ(\'2004-01-01 12:00:00\',\'+00:00\',\'+10:00\');\n        -> \'2004-01-01 22:00:00\'\n','date-and-time-functions'),(339,'TIME_TO_SEC',28,'Syntax:\nTIME_TO_SEC(time)\n\nReturns the time argument, converted to seconds.\n','mysql> SELECT TIME_TO_SEC(\'22:23:00\');\n        -> 80580\nmysql> SELECT TIME_TO_SEC(\'00:39:38\');\n        -> 2378\n','date-and-time-functions'),(340,'WEEKDAY',28,'Syntax:\nWEEKDAY(date)\n\nReturns the weekday index for date (0 = Monday, 1 = Tuesday, ... 6 =\nSunday).\n','mysql> SELECT WEEKDAY(\'1998-02-03 22:23:00\');\n        -> 1\nmysql> SELECT WEEKDAY(\'1997-11-05\');\n        -> 2\n','date-and-time-functions'),(341,'EXPORT_SET',33,'Syntax:\nEXPORT_SET(bits,on,off[,separator[,number_of_bits]])\n\nReturns a string such that for every bit set in the value bits, you get\nan on string and for every reset bit, you get an off string. Bits in\nbits are examined from right to left (from low-order to high-order\nbits). Strings are added to the result from left to right, separated by\nthe separator string (the default being the comma character `,\'). The\nnumber of bits examined is given by number_of_bits (defaults to 64).\n','mysql> SELECT EXPORT_SET(5,\'Y\',\'N\',\',\',4);\n        -> \'Y,N,Y,N\'\nmysql> SELECT EXPORT_SET(6,\'1\',\'0\',\',\',10);\n        -> \'0,1,1,0,0,0,0,0,0,0\'\n','string-functions'),(342,'TIME FUNCTION',28,'Syntax:\nTIME(expr)\n\nExtracts the time part of the time or datetime expression expr and\nreturns it as a string.\n','mysql> SELECT TIME(\'2003-12-31 01:02:03\');\n        -> \'01:02:03\'\nmysql> SELECT TIME(\'2003-12-31 01:02:03.000123\');\n        -> \'01:02:03.000123\'\n','date-and-time-functions'),(343,'CAST',33,'Syntax:\nCAST(expr AS type), CONVERT(expr,type), CONVERT(expr USING\ntranscoding_name)\n\nThe CAST() and CONVERT() functions take a value of one type and produce\na value of another type.\n\nThe type can be one of the following values:\n\no BINARY[(N)]\n\no CHAR[(N)]\n\no DATE\n\no DATETIME\n\no DECIMAL\n\no SIGNED [INTEGER]\n\no TIME\n\no UNSIGNED [INTEGER]\n\nBINARY produces a string with the BINARY data type. See\n[binary-varbinary] for a description of how this affects comparisons.\nIf the optional length N is given, BINARY(N) causes the cast to use no\nmore than N bytes of the argument. As of MySQL 5.0.17, values shorter\nthan N bytes are padded with 0x00 bytes to a length of N.\n\nCHAR(N) causes the cast to use no more than N characters of the\nargument.\n\nThe DECIMAL type is available as of MySQL 5.0.8.\n\nCAST() and CONVERT(... USING ...) are standard SQL syntax. The\nnon-USING form of CONVERT() is ODBC syntax.\n\nCONVERT() with USING is used to convert data between different\ncharacter sets. In MySQL, transcoding names are the same as the\ncorresponding character set names. For example, this statement converts\nthe string \'abc\' in the default character set to the corresponding\nstring in the utf8 character set:\n\nSELECT CONVERT(\'abc\' USING utf8);\n','SELECT enum_col FROM tbl_name ORDER BY CAST(enum_col AS CHAR);\n','cast-functions'),(344,'SOUNDS LIKE',33,'Syntax:\nexpr1 SOUNDS LIKE expr2\n\nThis is the same as SOUNDEX(expr1) = SOUNDEX(expr2).\n','','string-functions'),(345,'PERIOD_DIFF',28,'Syntax:\nPERIOD_DIFF(P1,P2)\n\nReturns the number of months between periods P1 and P2. P1 and P2\nshould be in the format YYMM or YYYYMM. Note that the period arguments\nP1 and P2 are not date values.\n','mysql> SELECT PERIOD_DIFF(9802,199703);\n        -> 11\n','date-and-time-functions'),(346,'LIKE',33,'Syntax:\nexpr LIKE pat [ESCAPE \'escape_char\']\n\nPattern matching using SQL simple regular expression comparison.\nReturns 1 (TRUE) or 0 (FALSE). If either expr or pat is NULL, the\nresult is NULL.\n\nThe pattern need not be a literal string. For example, it can be\nspecified as a string expression or table column.\n','mysql> SELECT \'David!\' LIKE \'David_\';\n        -> 1\nmysql> SELECT \'David!\' LIKE \'%D%v%\';\n        -> 1\n','string-comparison-functions'),(347,'MULTIPOINT',22,'MultiPoint(pt1,pt2,...)\n\nConstructs a WKB MultiPoint value using WKB Point arguments. If any\nargument is not a WKB Point, the return value is NULL.\n','','gis-mysql-specific-functions'),(348,'>>',18,'Syntax:\n>>\n\nShifts a longlong (BIGINT) number to the right.\n','mysql> SELECT 4 >> 2;\n        -> 1\n','bit-functions'),(349,'FETCH',35,'Syntax:\nFETCH cursor_name INTO var_name [, var_name] ...\n\nThis statement fetches the next row (if a row exists) using the\nspecified open cursor, and advances the cursor pointer.\n','','fetch'),(350,'TRUE FALSE',27,'The constants TRUE and FALSE evaluate to 1 and 0, respectively. The\nconstant names can be written in any lettercase.\n\nmysql> SELECT TRUE, true, FALSE, false;\n        -> 1, 1, 0, 0\n','','boolean-values'),(351,'AVG',14,'Syntax:\nAVG([DISTINCT] expr)\n\nReturns the average value of expr. The DISTINCT option can be used as\nof MySQL 5.0.3 to return the average of the distinct values of expr.\n\nAVG() returns NULL if there were no matching rows.\n','mysql> SELECT student_name, AVG(test_score)\n    ->        FROM student\n    ->        GROUP BY student_name;\n','group-by-functions'),(352,'MBRWITHIN',5,'MBRWithin(g1,g2)\n\nReturns 1 or 0 to indicate whether the Minimum Bounding Rectangle of g1\nis within the Minimum Bounding Rectangle of g2.\n','mysql> SET @g1 = GeomFromText(\'Polygon((0 0,0 3,3 3,3 0,0 0))\');\nmysql> SET @g2 = GeomFromText(\'Polygon((0 0,0 5,5 5,5 0,0 0))\');\nmysql> SELECT MBRWithin(@g1,@g2), MBRWithin(@g2,@g1);\n+--------------------+--------------------+\n| MBRWithin(@g1,@g2) | MBRWithin(@g2,@g1) |\n+--------------------+--------------------+\n|                  1 |                  0 |\n+--------------------+--------------------+\n','relations-on-geometry-mbr'),(353,'IN',17,'Syntax:\nexpr IN (value,...)\n\nReturns 1 if expr is equal to any of the values in the IN list, else\nreturns 0. If all values are constants, they are evaluated according to\nthe type of expr and sorted. The search for the item then is done using\na binary search. This means IN is very quick if the IN value list\nconsists entirely of constants. Otherwise, type conversion takes place\naccording to the rules described in [type-conversion], but applied to\nall the arguments.\n','mysql> SELECT 2 IN (0,3,5,\'wefwf\');\n        -> 0\nmysql> SELECT \'wefwf\' IN (0,3,5,\'wefwf\');\n        -> 1\n','comparison-operators'),(354,'QUOTE',33,'Syntax:\nQUOTE(str)\n\nQuotes a string to produce a result that can be used as a properly\nescaped data value in an SQL statement. The string is returned enclosed\nby single quotes and with each instance of single quote (`\'\'),\nbackslash (`\\\'), ASCII NUL, and Control-Z preceded by a backslash. If\nthe argument is NULL, the return value is the word \"NULL\" without\nenclosing single quotes.\n','mysql> SELECT QUOTE(\'Don\\\'t!\');\n        -> \'Don\\\'t!\'\nmysql> SELECT QUOTE(NULL);\n        -> NULL\n','string-functions'),(355,'SESSION_USER',15,'Syntax:\nSESSION_USER()\n\nSESSION_USER() is a synonym for USER().\n','','information-functions'),(356,'QUARTER',28,'Syntax:\nQUARTER(date)\n\nReturns the quarter of the year for date, in the range 1 to 4.\n','mysql> SELECT QUARTER(\'98-04-01\');\n        -> 2\n','date-and-time-functions'),(357,'POSITION',33,'Syntax:\nPOSITION(substr IN str)\n\nPOSITION(substr IN str) is a synonym for LOCATE(substr,str).\n','','string-functions'),(358,'IS_USED_LOCK',13,'Syntax:\nIS_USED_LOCK(str)\n\nChecks whether the lock named str is in use (that is, locked). If so,\nit returns the connection identifier of the client that holds the lock.\nOtherwise, it returns NULL.\n','','miscellaneous-functions'),(359,'POLYFROMTEXT',3,'PolyFromText(wkt[,srid]), PolygonFromText(wkt[,srid])\n\nConstructs a POLYGON value using its WKT representation and SRID.\n','','gis-wkt-functions'),(360,'DES_ENCRYPT',10,'Syntax:\nDES_ENCRYPT(str[,{key_num|key_str}])\n\nEncrypts the string with the given key using the Triple-DES algorithm.\n','key_num des_key_str\n','encryption-functions'),(361,'LENGTH',33,'Syntax:\nLENGTH(str)\n\nReturns the length of the string str, measured in bytes. A multi-byte\ncharacter counts as multiple bytes. This means that for a string\ncontaining five two-byte characters, LENGTH() returns 10, whereas\nCHAR_LENGTH() returns 5.\n','mysql> SELECT LENGTH(\'text\');\n        -> 4\n','string-functions'),(362,'STR_TO_DATE',28,'Syntax:\nSTR_TO_DATE(str,format)\n\nThis is the inverse of the DATE_FORMAT() function. It takes a string\nstr and a format string format. STR_TO_DATE() returns a DATETIME value\nif the format string contains both date and time parts, or a DATE or\nTIME value if the string contains only date or time parts.\n\nThe date, time, or datetime values contained in str should be given in\nthe format indicated by format. For the specifiers that can be used in\nformat, see the DATE_FORMAT() function description. If str contains an\nillegal date, time, or datetime value, STR_TO_DATE() returns NULL.\nStarting from MySQL 5.0.3, an illegal value also produces a warning.\n','','date-and-time-functions'),(363,'Y',9,'Y(p)\n\nReturns the Y-coordinate value for the point p as a double-precision\nnumber.\n','mysql> SET @pt = \'Point(56.7 53.34)\';\nmysql> SELECT Y(GeomFromText(@pt));\n+----------------------+\n| Y(GeomFromText(@pt)) |\n+----------------------+\n|                53.34 |\n+----------------------+\n','point-property-functions'),(364,'SHOW INNODB STATUS',25,'Syntax:\nSHOW INNODB STATUS\n\nIn MySQL 5.0, this is a deprecated synonym for SHOW ENGINE INNODB\nSTATUS. See [show-engine].\n','','show-innodb-status'),(365,'CHECKSUM TABLE',19,'Syntax:\nCHECKSUM TABLE tbl_name [, tbl_name] ... [ QUICK | EXTENDED ]\n\nCHECKSUM TABLE reports a table checksum.\n\nWith QUICK, the live table checksum is reported if it is available, or\nNULL otherwise. This is very fast. A live checksum is enabled by\nspecifying the CHECKSUM=1 table option when you create the table;\ncurrently, this is supported only for MyISAM tables. See\n[create-table].\n\nWith EXTENDED, the entire table is read row by row and the checksum is\ncalculated. This can be very slow for large tables.\n\nIf neither QUICK nor EXTENDED is specified, MySQL returns a live\nchecksum if the table storage engine supports it and scans the table\notherwise.\n\nFor a non-existent table, CHECKSUM TABLE returns NULL and, as of MySQL\n5.0.3, generates a warning.\n','','checksum-table'),(366,'NUMINTERIORRINGS',2,'NumInteriorRings(poly)\n\nReturns the number of interior rings in the Polygon value poly.\n','mysql> SET @poly =\n    -> \'Polygon((0 0,0 3,3 3,3 0,0 0),(1 1,1 2,2 2,2 1,1 1))\';\nmysql> SELECT NumInteriorRings(GeomFromText(@poly));\n+---------------------------------------+\n| NumInteriorRings(GeomFromText(@poly)) |\n+---------------------------------------+\n|                                     1 |\n+---------------------------------------+\n','polygon-property-functions'),(367,'INTERIORRINGN',2,'InteriorRingN(poly,N)\n\nReturns the N-th interior ring for the Polygon value poly as a\nLineString. Rings are numbered beginning with 1.\n','mysql> SET @poly =\n    -> \'Polygon((0 0,0 3,3 3,3 0,0 0),(1 1,1 2,2 2,2 1,1 1))\';\nmysql> SELECT AsText(InteriorRingN(GeomFromText(@poly),1));\n+----------------------------------------------+\n| AsText(InteriorRingN(GeomFromText(@poly),1)) |\n+----------------------------------------------+\n| LINESTRING(1 1,1 2,2 2,2 1,1 1)              |\n+----------------------------------------------+\n','polygon-property-functions'),(368,'UTC_TIME',28,'Syntax:\nUTC_TIME, UTC_TIME()\n\nReturns the current UTC time as a value in \'HH:MM:SS\' or HHMMSS format,\ndepending on whether the function is used in a string or numeric\ncontext.\n','mysql> SELECT UTC_TIME(), UTC_TIME() + 0;\n        -> \'18:07:53\', 180753\n','date-and-time-functions'),(369,'DROP FUNCTION',34,'Syntax:\nDROP FUNCTION function_name\n\nThis statement drops the user-defined function (UDF) named\nfunction_name.\n\nTo drop a function, you must have the DELETE privilege for the mysql\ndatabase. This is because DROP FUNCTION removes a row from the\nmysql.func system table that records the function\'s name, type, and\nshared library name.\n','','drop-function'),(370,'STDDEV',14,'Syntax:\nSTD(expr) STDDEV(expr)\n\nReturns the population standard deviation of expr. This is an extension\nto standard SQL. The STDDEV() form of this function is provided for\ncompatibility with Oracle. As of MySQL 5.0.3, the standard SQL function\nSTDDEV_POP() can be used instead.\n\nThese functions return NULL if there were no matching rows.\n','','group-by-functions'),(371,'PERIOD_ADD',28,'Syntax:\nPERIOD_ADD(P,N)\n\nAdds N months to period P (in the format YYMM or YYYYMM). Returns a\nvalue in the format YYYYMM. Note that the period argument P is not a\ndate value.\n','mysql> SELECT PERIOD_ADD(9801,2);\n        -> 199803\n','date-and-time-functions'),(372,'|',18,'Syntax:\n|\n\nBitwise OR:\n','mysql> SELECT 29 | 15;\n        -> 31\n','bit-functions'),(373,'GEOMFROMTEXT',3,'GeomFromText(wkt[,srid]), GeometryFromText(wkt[,srid])\n\nConstructs a geometry value of any type using its WKT representation\nand SRID.\n','','gis-wkt-functions'),(374,'RIGHT',33,'Syntax:\nRIGHT(str,len)\n\nReturns the rightmost len characters from the string str.\n','mysql> SELECT RIGHT(\'foobarbar\', 4);\n        -> \'rbar\'\n','string-functions'),(375,'DATEDIFF',28,'Syntax:\nDATEDIFF(expr,expr2)\n\nDATEDIFF() returns the number of days between the start date expr and\nthe end date expr2. expr and expr2 are date or date-and-time\nexpressions. Only the date parts of the values are used in the\ncalculation.\n','mysql> SELECT DATEDIFF(\'1997-12-31 23:59:59\',\'1997-12-30\');\n        -> 1\nmysql> SELECT DATEDIFF(\'1997-11-30 23:59:59\',\'1997-12-31\');\n        -> -31\n','date-and-time-functions'),(376,'DROP PROCEDURE',35,'Syntax:\nDROP {PROCEDURE | FUNCTION} [IF EXISTS] sp_name\n\nThis statement is used to drop a stored procedure or function. That is,\nthe specified routine is removed from the server. As of MySQL 5.0.3,\nyou must have the ALTER ROUTINE privilege for the routine. (That\nprivilege is granted automatically to the routine creator.)\n\nThe IF EXISTS clause is a MySQL extension. It prevents an error from\noccurring if the procedure or function does not exist. A warning is\nproduced that can be viewed with SHOW WARNINGS.\n','','drop-procedure'),(377,'CHECK TABLE',19,'Syntax:\nCHECK TABLE tbl_name [, tbl_name] ... [option] ...\n\noption = {FOR UPGRADE | QUICK | FAST | MEDIUM | EXTENDED | CHANGED}\n\nCHECK TABLE checks a table or tables for errors. CHECK TABLE works for\nMyISAM, InnoDB, and (as of MySQL 5.0.16) ARCHIVE tables. For MyISAM\ntables, the key statistics are updated as well.\n\nAs of MySQL 5.0.2, CHECK TABLE can also check views for problems, such\nas tables that are referenced in the view definition that no longer\nexist.\n','','check-table'),(378,'BIN',33,'Syntax:\nBIN(N)\n\nReturns a string representation of the binary value of N, where N is a\nlonglong (BIGINT) number. This is equivalent to CONV(N,10,2). Returns\nNULL if N is NULL.\n','mysql> SELECT BIN(12);\n        -> \'1100\'\n','string-functions'),(379,'CASE FUNCTION',6,'Syntax:\nCASE value WHEN [compare_value] THEN result [WHEN [compare_value] THEN\nresult ...] [ELSE result] END\n\nCASE WHEN [condition] THEN result [WHEN [condition] THEN result ...]\n[ELSE result] END\n\nThe first version returns the result where value=compare_value. The\nsecond version returns the result for the first condition that is true.\nIf there was no matching result value, the result after ELSE is\nreturned, or NULL if there is no ELSE part.\n','mysql> SELECT CASE 1 WHEN 1 THEN \'one\'\n    ->     WHEN 2 THEN \'two\' ELSE \'more\' END;\n        -> \'one\'\nmysql> SELECT CASE WHEN 1>0 THEN \'true\' ELSE \'false\' END;\n        -> \'true\'\nmysql> SELECT CASE BINARY \'B\'\n    ->     WHEN \'a\' THEN 1 WHEN \'b\' THEN 2 END;\n        -> NULL\n','control-flow-functions'),(380,'DECLARE CURSOR',35,'Syntax:\nDECLARE cursor_name CURSOR FOR select_statement\n\nThis statement declares a cursor. Multiple cursors may be declared in a\nroutine, but each cursor in a given block must have a unique name.\n\nThe SELECT statement cannot have an INTO clause.\n','','declare-cursors'),(381,'MULTILINESTRING',22,'MultiLineString(ls1,ls2,...)\n\nConstructs a WKB MultiLineString value using WKB LineString arguments.\nIf any argument is not a WKB LineString, the return value is NULL.\n','','gis-mysql-specific-functions'),(382,'LOAD DATA',25,'Syntax:\nLOAD DATA [LOW_PRIORITY | CONCURRENT] [LOCAL] INFILE \'file_name\'\n    [REPLACE | IGNORE]\n    INTO TABLE tbl_name\n    [FIELDS\n        [TERMINATED BY \'string\']\n        [[OPTIONALLY] ENCLOSED BY \'char\']\n        [ESCAPED BY \'char\']\n    ]\n    [LINES\n        [STARTING BY \'string\']\n        [TERMINATED BY \'string\']\n    ]\n    [IGNORE number LINES]\n    [(col_name_or_user_var,...)]\n    [SET col_name = expr,...)]\n\nThe LOAD DATA INFILE statement reads rows from a text file into a table\nat a very high speed. The filename must be given as a literal string.\n\nLOAD DATA INFILE is the complement of SELECT ... INTO OUTFILE. (See\n[select].) To write data from a table to a file, use SELECT ... INTO\nOUTFILE. To read the file back into a table, use LOAD DATA INFILE. The\nsyntax of the FIELDS and LINES clauses is the same for both statements.\nBoth clauses are optional, but FIELDS must precede LINES if both are\nspecified.\n\nFor more information about the efficiency of INSERT versus LOAD DATA\nINFILE and speeding up LOAD DATA INFILE, see [insert-speed].\n\nThe character set indicated by the character_set_database system\nvariable is used to interpret the information in the file. SET NAMES\nand the setting of character_set_client do not affect interpretation of\ninput.\n\nNote that it is currently not possible to load data files that use the\nucs2 character set.\n\nAs of MySQL 5.0.19, the character_set_filesystem system variable\ncontrols the interpretation of the filename.\n\nYou can also load data files by using the mysqlimport utility; it\noperates by sending a LOAD DATA INFILE statement to the server. The\n--local option causes mysqlimport to read data files from the client\nhost. You can specify the --compress option to get better performance\nover slow networks if the client and server support the compressed\nprotocol. See [mysqlimport].\n\nIf you use LOW_PRIORITY, execution of the LOAD DATA statement is\ndelayed until no other clients are reading from the table.\n\nIf you specify CONCURRENT with a MyISAM table that satisfies the\ncondition for concurrent inserts (that is, it contains no free blocks\nin the middle), other threads can retrieve data from the table while\nLOAD DATA is executing. Using this option affects the performance of\nLOAD DATA a bit, even if no other thread is using the table at the same\ntime.\n\nThe LOCAL keyword, if specified, is interpreted with respect to the\nclient end of the connection:\n\no If LOCAL is specified, the file is read by the client program on the\n  client host and sent to the server. The file can be given as a full\n  pathname to specify its exact location. If given as a relative\n  pathname, the name is interpreted relative to the directory in which\n  the client program was started.\n\no If LOCAL is not specified, the file must be located on the server\n  host and is read directly by the server. The server uses the\n  following rules to locate the file:\n\n  o If the filename is an absolute pathname, the server uses it as\n    given.\n\n  o If the filename is a relative pathname with one or more leading\n    components, the server searches for the file relative to the\n    server\'s data directory.\n\n  o If a filename with no leading components is given, the server looks\n    for the file in the database directory of the default database.\n\nNote that, in the non-LOCAL case, these rules mean that a file named as\n./myfile.txt is read from the server\'s data directory, whereas the file\nnamed as myfile.txt is read from the database directory of the default\ndatabase. For example, if db1 is the default database, the following\nLOAD DATA statement reads the file data.txt from the database directory\nfor db1, even though the statement explicitly loads the file into a\ntable in the db2 database:\n\nLOAD DATA INFILE \'data.txt\' INTO TABLE db2.my_table;\n\nWindows pathnames are specified using forward slashes rather than\nbackslashes. If you do use backslashes, you must double them.\n\nFor security reasons, when reading text files located on the server,\nthe files must either reside in the database directory or be readable\nby all. Also, to use LOAD DATA INFILE on server files, you must have\nthe FILE privilege. See [privileges-provided].\n','','load-data'),(383,'LOCALTIME',28,'Syntax:\nLOCALTIME, LOCALTIME()\n\nLOCALTIME and LOCALTIME() are synonyms for NOW().\n','','date-and-time-functions'),(384,'MPOINTFROMTEXT',3,'MPointFromText(wkt[,srid]), MultiPointFromText(wkt[,srid])\n\nConstructs a MULTIPOINT value using its WKT representation and SRID.\n','','gis-wkt-functions'),(385,'BLOB',20,'BLOB[(M)]\n\nA BLOB column with a maximum length of 65,535 (216 - 1) bytes.\n\nAn optional length M can be given for this type. If this is done, MySQL\ncreates the column as the smallest BLOB type large enough to hold\nvalues M bytes long.\n','','string-type-overview'),(386,'PASSWORD',10,'Syntax:\nPASSWORD(str)\n\nCalculates and returns a password string from the plaintext password\nstr and returns a binary string, or NULL if the argument was NULL. This\nis the function that is used for encrypting MySQL passwords for storage\nin the Password column of the user grant table.\n','mysql> SELECT PASSWORD(\'badpwd\');\n        -> \'*AAB3E285149C0135D51A520E1940DD3263DC008C\'\n','encryption-functions'),(387,'CHAR',20,'[NATIONAL] CHAR(M) [BINARY | ASCII | UNICODE]\n\nA fixed-length string that is always right-padded with spaces to the\nspecified length when stored. M represents the column length. The range\nof M is 0 to 255 characters.\n\nNote: Trailing spaces are removed when CHAR values are retrieved.\n\nBefore MySQL 5.0.3, a CHAR column with a length specification greater\nthan 255 is converted to the smallest TEXT type that can hold values of\nthe given length. For example, CHAR(500) is converted to TEXT, and\nCHAR(200000) is converted to MEDIUMTEXT. This is a compatibility\nfeature. However, this conversion causes the column to become a\nvariable-length column, and also affects trailing-space removal.\n\nIn MySQL 5.0.3 and later, if you attempt to set the length of a CHAR\ngreater than 255, the CREATE TABLE or ALTER TABLE statement in which\nthis is done fails with an error:\n\nmysql> CREATE TABLE c1 (col1 INT, col2 CHAR(500));\nERROR 1074 (42000): Column length too big for column \'col\' (max = 255);\nuse BLOB or TEXT instead\nmysql> SHOW CREATE TABLE c1;\nERROR 1146 (42S02): Table \'test.c1\' doesn\'t exist\n','','string-type-overview'),(388,'UTC_DATE',28,'Syntax:\nUTC_DATE, UTC_DATE()\n\nReturns the current UTC date as a value in \'YYYY-MM-DD\' or YYYYMMDD\nformat, depending on whether the function is used in a string or\nnumeric context.\n','mysql> SELECT UTC_DATE(), UTC_DATE() + 0;\n        -> \'2003-08-14\', 20030814\n','date-and-time-functions'),(389,'DIMENSION',32,'Dimension(g)\n\nReturns the inherent dimension of the geometry value g. The result can\nbe -1, 0, 1, or 2. The meaning of these values is given in\n[gis-class-geometry].\n','mysql> SELECT Dimension(GeomFromText(\'LineString(1 1,2 2)\'));\n+------------------------------------------------+\n| Dimension(GeomFromText(\'LineString(1 1,2 2)\')) |\n+------------------------------------------------+\n|                                              1 |\n+------------------------------------------------+\n','general-geometry-property-functions'),(390,'COUNT DISTINCT',14,'Syntax:\nCOUNT(DISTINCT expr,[expr...])\n\nReturns a count of the number of different non-NULL values.\n\nCOUNT(DISTINCT) returns 0 if there were no matching rows.\n','mysql> SELECT COUNT(DISTINCT results) FROM student;\n','group-by-functions'),(391,'BIT',20,'BIT[(M)]\n\nA bit-field type. M indicates the number of bits per value, from 1 to\n64. The default is 1 if M is omitted.\n\nThis data type was added in MySQL 5.0.3 for MyISAM, and extended in\n5.0.5 to MEMORY, InnoDB, and BDB. Before 5.0.3, BIT is a synonym for\nTINYINT(1).\n','','numeric-type-overview'),(392,'EQUALS',26,'Equals(g1,g2)\n\nReturns 1 or 0 to indicate whether g1 is spatially equal to g2.\n','','functions-that-test-spatial-relationships-between-geometries'),(393,'SHOW CREATE VIEW',25,'Syntax:\nSHOW CREATE VIEW view_name\n\nThis statement shows a CREATE VIEW statement that creates the given\nview.\n','','show-create-view'),(394,'INTERVAL',17,'Syntax:\nINTERVAL(N,N1,N2,N3,...)\n\nReturns 0 if N < N1, 1 if N < N2 and so on or -1 if N is NULL. All\narguments are treated as integers. It is required that N1 < N2 < N3 <\n... < Nn for this function to work correctly. This is because a binary\nsearch is used (very fast).\n','mysql> SELECT INTERVAL(23, 1, 15, 17, 30, 44, 200);\n        -> 3\nmysql> SELECT INTERVAL(10, 1, 10, 100, 1000);\n        -> 2\nmysql> SELECT INTERVAL(22, 23, 30, 44, 200);\n        -> 0\n','comparison-operators'),(395,'FROM_DAYS',28,'Syntax:\nFROM_DAYS(N)\n\nGiven a day number N, returns a DATE value.\n','mysql> SELECT FROM_DAYS(729669);\n        -> \'1997-10-07\'\n','date-and-time-functions'),(396,'ALTER PROCEDURE',35,'Syntax:\nALTER {PROCEDURE | FUNCTION} sp_name [characteristic ...]\n\ncharacteristic:\n    { CONTAINS SQL | NO SQL | READS SQL DATA | MODIFIES SQL DATA }\n  | SQL SECURITY { DEFINER | INVOKER }\n  | COMMENT \'string\'\n\nThis statement can be used to change the characteristics of a stored\nprocedure or function. As of MySQL 5.0.3, you must have the ALTER\nROUTINE privilege for the routine. (That privilege is granted\nautomatically to the routine creator.) If binary logging is enabled,\nthis statement might also require the SUPER privilege, as described in\n[stored-procedure-logging].\n\nMore than one change may be specified in an ALTER PROCEDURE or ALTER\nFUNCTION statement.\n','','alter-procedure'),(397,'BIT_COUNT',18,'Syntax:\nBIT_COUNT(N)\n\nReturns the number of bits that are set in the argument N.\n','mysql> SELECT BIT_COUNT(29), BIT_COUNT(b\'101010\');\n        -> 4, 3\n','bit-functions'),(398,'UTC_TIMESTAMP',28,'Syntax:\nUTC_TIMESTAMP, UTC_TIMESTAMP()\n\nReturns the current UTC date and time as a value in \'YYYY-MM-DD\nHH:MM:SS\' or YYYYMMDDHHMMSS format, depending on whether the function\nis used in a string or numeric context.\n','mysql> SELECT UTC_TIMESTAMP(), UTC_TIMESTAMP() + 0;\n        -> \'2003-08-14 18:08:04\', 20030814180804\n','date-and-time-functions'),(399,'+',4,'Syntax:\n+\n\nAddition:\n','mysql> SELECT 3+5;\n        -> 8\n','arithmetic-functions'),(400,'INET_NTOA',13,'Syntax:\nINET_NTOA(expr)\n\nGiven a numeric network address (4 or 8 byte), returns the dotted-quad\nrepresentation of the address as a string.\n','mysql> SELECT INET_NTOA(3520061480);\n        -> \'209.207.224.40\'\n','miscellaneous-functions'),(401,'ACOS',4,'Syntax:\nACOS(X)\n\nReturns the arc cosine of X, that is, the value whose cosine is X.\nReturns NULL if X is not in the range -1 to 1.\n','mysql> SELECT ACOS(1);\n        -> 0\nmysql> SELECT ACOS(1.0001);\n        -> NULL\nmysql> SELECT ACOS(0);\n        -> 1.5707963267949\n','mathematical-functions'),(402,'ISOLATION',7,'Syntax:\nSET [GLOBAL | SESSION] TRANSACTION ISOLATION LEVEL\n{ READ UNCOMMITTED | READ COMMITTED | REPEATABLE READ | SERIALIZABLE }\n\nThis statement sets the transaction isolation level for the next\ntransaction, globally, or for the current session.\n\nThe default behavior of SET TRANSACTION is to set the isolation level\nfor the next (not yet started) transaction. If you use the GLOBAL\nkeyword, the statement sets the default transaction level globally for\nall new connections created from that point on. Existing connections\nare unaffected. You need the SUPER privilege to do this. Using the\nSESSION keyword sets the default transaction level for all future\ntransactions performed on the current connection.\n\nFor descriptions of each InnoDB transaction isolation level, see\n[innodb-transaction-isolation]. InnoDB supports each of these levels in\nMySQL 5.0. The default level is REPEATABLE READ.\n\nTo set the initial default global isolation level for mysqld, use the\n--transaction-isolation option. See [server-options].\n','','set-transaction'),(403,'CEILING',4,'Syntax:\nCEILING(X), CEIL(X)\n\nReturns the smallest integer value not less than X.\n','mysql> SELECT CEILING(1.23);\n        -> 2\nmysql> SELECT CEIL(-1.23);\n        -> -1\n','mathematical-functions'),(404,'SIN',4,'Syntax:\nSIN(X)\n\nReturns the sine of X, where X is given in radians.\n','mysql> SELECT SIN(PI());\n        -> 1.2246063538224e-16\nmysql> SELECT ROUND(SIN(PI()));\n        -> 0\n','mathematical-functions'),(405,'DAYOFWEEK',28,'Syntax:\nDAYOFWEEK(date)\n\nReturns the weekday index for date (1 = Sunday, 2 = Monday, ..., 7 =\nSaturday). These index values correspond to the ODBC standard.\n','mysql> SELECT DAYOFWEEK(\'1998-02-03\');\n        -> 3\n','date-and-time-functions'),(406,'LINEFROMWKB',29,'LineFromWKB(wkb[,srid]), LineStringFromWKB(wkb[,srid])\n\nConstructs a LINESTRING value using its WKB representation and SRID.\n','','gis-wkb-functions'),(407,'SHOW PROCESSLIST',25,'Syntax:\nSHOW [FULL] PROCESSLIST\n\nSHOW PROCESSLIST shows you which threads are running. You can also get\nthis information using the mysqladmin processlist command. If you have\nthe SUPER privilege, you can see all threads. Otherwise, you can see\nonly your own threads (that is, threads associated with the MySQL\naccount that you are using). See [kill]. If you do not use the FULL\nkeyword, only the first 100 characters of each statement are shown in\nthe Info field.\n','','show-processlist'),(408,'GEOMETRYTYPE',32,'GeometryType(g)\n\nReturns as a string the name of the geometry type of which the geometry\ninstance g is a member. The name corresponds to one of the instantiable\nGeometry subclasses.\n','mysql> SELECT GeometryType(GeomFromText(\'POINT(1 1)\'));\n+------------------------------------------+\n| GeometryType(GeomFromText(\'POINT(1 1)\')) |\n+------------------------------------------+\n| POINT                                    |\n+------------------------------------------+\n','general-geometry-property-functions'),(409,'CREATE VIEW',36,'Syntax:\nCREATE\n    [OR REPLACE]\n    [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}]\n    [DEFINER = { user | CURRENT_USER }]\n    [SQL SECURITY { DEFINER | INVOKER }]\n    VIEW view_name [(column_list)]\n    AS select_statement\n    [WITH [CASCADED | LOCAL] CHECK OPTION]\n\nThis statement creates a new view, or replaces an existing one if the\nOR REPLACE clause is given. The select_statement is a SELECT statement\nthat provides the definition of the view. The statement can select from\nbase tables or other views.\n\nThis statement requires the CREATE VIEW privilege for the view, and\nsome privilege for each column selected by the SELECT statement. For\ncolumns used elsewhere in the SELECT statement you must have the SELECT\nprivilege. If the OR REPLACE clause is present, you must also have the\nDROP privilege for the view.\n\nA view belongs to a database. By default, a new view is created in the\ndefault database. To create the view explicitly in a given database,\nspecify the name as db_name.view_name when you create it.\n\nmysql> CREATE VIEW test.v AS SELECT * FROM t;\n\nBase tables and views share the same namespace within a database, so a\ndatabase cannot contain a base table and a view that have the same\nname.\n\nViews must have unique column names with no duplicates, just like base\ntables. By default, the names of the columns retrieved by the SELECT\nstatement are used for the view column names. To define explicit names\nfor the view columns, the optional column_list clause can be given as a\nlist of comma-separated identifiers. The number of names in column_list\nmust be the same as the number of columns retrieved by the SELECT\nstatement.\n\nColumns retrieved by the SELECT statement can be simple references to\ntable columns. They can also be expressions that use functions,\nconstant values, operators, and so forth.\n\nUnqualified table or view names in the SELECT statement are interpreted\nwith respect to the default database. A view can refer to tables or\nviews in other databases by qualifying the table or view name with the\nproper database name.\n\nA view can be created from many kinds of SELECT statements. It can\nrefer to base tables or other views. It can use joins, UNION, and\nsubqueries. The SELECT need not even refer to any tables. The following\nexample defines a view that selects two columns from another table, as\nwell as an expression calculated from those columns:\n\nmysql> CREATE TABLE t (qty INT, price INT);\nmysql> INSERT INTO t VALUES(3, 50);\nmysql> CREATE VIEW v AS SELECT qty, price, qty*price AS value FROM t;\nmysql> SELECT * FROM v;\n+------+-------+-------+\n| qty  | price | value |\n+------+-------+-------+\n|    3 |    50 |   150 |\n+------+-------+-------+\n\nA view definition is subject to the following restrictions:\n\no The SELECT statement cannot contain a subquery in the FROM clause.\n\no The SELECT statement cannot refer to system or user variables.\n\no The SELECT statement cannot refer to prepared statement parameters.\n\no Within a stored routine, the definition cannot refer to routine\n  parameters or local variables.\n\no Any table or view referred to in the definition must exist. However,\n  after a view has been created, it is possible to drop a table or view\n  that the definition refers to. To check a view definition for\n  problems of this kind, use the CHECK TABLE statement.\n\no The definition cannot refer to a TEMPORARY table, and you cannot\n  create a TEMPORARY view.\n\no The tables named in the view definition must already exist.\n\no You cannot associate a trigger with a view.\n\nORDER BY is allowed in a view definition, but it is ignored if you\nselect from a view using a statement that has its own ORDER BY.\n\nFor other options or clauses in the definition, they are added to the\noptions or clauses of the statement that references the view, but the\neffect is undefined. For example, if a view definition includes a LIMIT\nclause, and you select from the view using a statement that has its own\nLIMIT clause, it is undefined which limit applies. This same principle\napplies to options such as ALL, DISTINCT, or SQL_SMALL_RESULT that\nfollow the SELECT keyword, and to clauses such as INTO, FOR UPDATE,\nLOCK IN SHARE MODE, and PROCEDURE.\n\nIf you create a view and then change the query processing environment\nby changing system variables, that may affect the results that you get\nfrom the view:\n\nmysql> CREATE VIEW v AS SELECT CHARSET(CHAR(65)), COLLATION(CHAR(65));\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> SET NAMES \'latin1\';\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> SELECT * FROM v;\n+-------------------+---------------------+\n| CHARSET(CHAR(65)) | COLLATION(CHAR(65)) |\n+-------------------+---------------------+\n| latin1            | latin1_swedish_ci   |\n+-------------------+---------------------+\n1 row in set (0.00 sec)\n\nmysql> SET NAMES \'utf8\';\nQuery OK, 0 rows affected (0.00 sec)\n\nmysql> SELECT * FROM v;\n+-------------------+---------------------+\n| CHARSET(CHAR(65)) | COLLATION(CHAR(65)) |\n+-------------------+---------------------+\n| utf8              | utf8_general_ci     |\n+-------------------+---------------------+\n1 row in set (0.00 sec)\n\nThe DEFINER and SQL SECURITY clauses specify the security context to be\nused when checking access privileges at view invocation time. They were\naddded in MySQL 5.0.13, but have no effect until MySQL 5.0.16.\n\nCURRENT_USER also can be given as CURRENT_USER().\n\nWithin a stored routine that is defined with the SQL SECURITY DEFINER\ncharacteristic, CURRENT_USER returns the routine creator. This also\naffects a view defined within such a routine, if the view definition\ncontains a DEFINER value of CURRENT_USER.\n\nThe default DEFINER value is the user who executes the CREATE VIEW\nstatement. (This is the same as DEFINER = CURRENT_USER.) If a user\nvalue is given, it should be a MySQL account in \'user_name\'@\'host_name\'\nformat (the same format used in the GRANT statement). The user_name and\nhost_name values both are required.\n\nIf you specify the DEFINER clause, you cannot set the value to any user\nbut your own unless you have the SUPER privilege. These rules determine\nthe legal DEFINER user values:\n\no If you do not have the SUPER privilege, the only legal user value is\n  your own account, either specified literally or by using\n  CURRENT_USER. You cannot set the definer to some other account.\n\no If you have the SUPER privilege, you can specify any syntactically\n  legal account name. If the account does not actually exist, a warning\n  is generated.\n\nThe SQL SECURITY characteristic determines which MySQL account to use\nwhen checking access privileges for the view when the view is executed.\nThe legal characteristic values are DEFINER and INVOKER. These indicate\nthat the view must be executable by the user who defined it or invoked\nit, respectively. The default SQL SECURITY value is DEFINER.\n\nAs of MySQL 5.0.16 (when the DEFINER and SQL SECURITY clauses were\nimplemented), view privileges are checked like this:\n\no At view definition time, the view creator must have the privileges\n  needed to use the top-level objects accessed by the view. For\n  example, if the view definition refers to a stored function, only the\n  privileges needed to invoke the function can be checked. The\n  privileges required when the function runs can be checked only as it\n  executes: For different invocations of the function, different\n  execution paths within the function might be taken.\n\no At view execution time, privileges for objects accessed by the view\n  are checked against the privileges held by the view creator or\n  invoker, depending on whether the SQL SECURITY characteristic is\n  DEFINER or INVOKER, respectively.\n\no If view execution causes execution of a stored function, privilege\n  checking for statements executed within the function depend on\n  whether the function is defined with a SQL SECURITY characteristic of\n  DEFINER or INVOKER. If the security characteristic is DEFINER, the\n  function runs with the privileges of its creator. If the\n  characteristic is INVOKER, the function runs with the privileges\n  determined by the view\'s SQL SECURITY characteristic.\n\nPrior to MySQL 5.0.16 (before the DEFINER and SQL SECURITY clauses were\nimplemented), privileges required for objects used in a view are\nchecked at view creation time.\n\nExample: A view might depend on a stored function, and that function\nmight invoke other stored routines. For example, the following view\ninvokes a stored function f():\n\nCREATE VIEW v AS SELECT * FROM t WHERE t.id = f(t.name);\n\nSuppose that f() contains a statement such as this:\n\nIF name IS NULL then\n  CALL p1();\nELSE\n  CALL p2();\nEND IF;\n\nThe privileges required for executing statements within f() need to be\nchecked when f() executes. This might mean that privileges are needed\nfor p1() or p2(), depending on the execution path within f(). Those\nprivileges need to be checked at runtime, and the user who must possess\nthe privileges is determined by the SQL SECURITY values of the function\nf() and the view v.\n\nThe DEFINER and SQL SECURITY clauses for views are extensions to\nstandard SQL. In standard SQL, views are handled using the rules for\nSQL SECURITY INVOKER.\n\nIf you invoke a view that was created before MySQL 5.0.13, it is\ntreated as though it was created with a SQL SECURITY INVOKER clause and\nwith a DEFINER value that is the same as your account. However, because\nthe actual definer is unknown, MySQL issues a warning. To make the\nwarning go away, it is sufficient to re-create the view so that the\nview definition includes a DEFINER clause.\n\nThe optional ALGORITHM clause is a MySQL extension to standard SQL.\nALGORITHM takes three values: MERGE, TEMPTABLE, or UNDEFINED. The\ndefault algorithm is UNDEFINED if no ALGORITHM clause is present. The\nalgorithm affects how MySQL processes the view.\n\nFor MERGE, the text of a statement that refers to the view and the view\ndefinition are merged such that parts of the view definition replace\ncorresponding parts of the statement.\n\nFor TEMPTABLE, the results from the view are retrieved into a temporary\ntable, which then is used to execute the statement.\n\nFor UNDEFINED, MySQL chooses which algorithm to use. It prefers MERGE\nover TEMPTABLE if possible, because MERGE is usually more efficient and\nbecause a view cannot be updatable if a temporary table is used.\n\nA reason to choose TEMPTABLE explicitly is that locks can be released\non underlying tables after the temporary table has been created and\nbefore it is used to finish processing the statement. This might result\nin quicker lock release than the MERGE algorithm so that other clients\nthat use the view are not blocked as long.\n\nA view algorithm can be UNDEFINED for three reasons:\n\no No ALGORITHM clause is present in the CREATE VIEW statement.\n\no The CREATE VIEW statement has an explicit ALGORITHM = UNDEFINED\n  clause.\n\no ALGORITHM = MERGE is specified for a view that can be processed only\n  with a temporary table. In this case, MySQL generates a warning and\n  sets the algorithm to UNDEFINED.\n\nAs mentioned earlier, MERGE is handled by merging corresponding parts\nof a view definition into the statement that refers to the view. The\nfollowing examples briefly illustrate how the MERGE algorithm works.\nThe examples assume that there is a view v_merge that has this\ndefinition:\n\nCREATE ALGORITHM = MERGE VIEW v_merge (vc1, vc2) AS\nSELECT c1, c2 FROM t WHERE c3 > 100;\n\nExample 1: Suppose that we issue this statement:\n\nSELECT * FROM v_merge;\n\nMySQL handles the statement as follows:\n\no v_merge becomes t\n\no * becomes vc1, vc2, which corresponds to c1, c2\n\no The view WHERE clause is added\n\nThe resulting statement to be executed becomes:\n\nSELECT c1, c2 FROM t WHERE c3 > 100;\n\nExample 2: Suppose that we issue this statement:\n\nSELECT * FROM v_merge WHERE vc1 < 100;\n\nThis statement is handled similarly to the previous one, except that\nvc1 < 100 becomes c1 < 100 and the view WHERE clause is added to the\nstatement WHERE clause using an AND connective (and parentheses are\nadded to make sure the parts of the clause are executed with correct\nprecedence). The resulting statement to be executed becomes:\n\nSELECT c1, c2 FROM t WHERE (c3 > 100) AND (c1 < 100);\n\nEffectively, the statement to be executed has a WHERE clause of this\nform:\n\nWHERE (select WHERE) AND (view WHERE)\n\nThe MERGE algorithm requires a one-to relationship between the rows in\nthe view and the rows in the underlying table. If this relationship\ndoes not hold, a temporary table must be used instead. Lack of a\none-to-one relationship occurs if the view contains any of a number of\nconstructs:\n\no Aggregate functions (SUM(), MIN(), MAX(), COUNT(), and so forth)\n\no DISTINCT\n\no GROUP BY\n\no HAVING\n\no UNION or UNION ALL\n\no Refers only to literal values (in this case, there is no underlying\n  table)\n\nSome views are updatable. That is, you can use them in statements such\nas UPDATE, DELETE, or INSERT to update the contents of the underlying\ntable. For a view to be updatable, there must be a one-to relationship\nbetween the rows in the view and the rows in the underlying table.\nThere are also certain other constructs that make a view non-updatable.\nTo be more specific, a view is not updatable if it contains any of the\nfollowing:\n\no Aggregate functions (SUM(), MIN(), MAX(), COUNT(), and so forth)\n\no DISTINCT\n\no GROUP BY\n\no HAVING\n\no UNION or UNION ALL\n\no Subquery in the select list\n\no Join\n\no Non-updatable view in the FROM clause\n\no A subquery in the WHERE clause that refers to a table in the FROM\n  clause\n\no Refers only to literal values (in this case, there is no underlying\n  table to update)\n\no ALGORITHM = TEMPTABLE (use of a temporary table always makes a view\n  non-updatable)\n\nWith respect to insertability (being updatable with INSERT statements),\nan updatable view is insertable if it also satisfies these additional\nrequirements for the view columns:\n\no There must be no duplicate view column names.\n\no The view must contain all columns in the base table that do not have\n  a default value.\n\no The view columns must be simple column references and not derived\n  columns. A derived column is one that is not a simple column\n  reference but is derived from an expression. These are examples of\n  derived columns:\n\n3.14159\ncol1 + 3\nUPPER(col2)\ncol3 / col4\n(subquery)\n\nA view that has a mix of simple column references and derived columns\nis not insertable, but it can be updatable if you update only those\ncolumns that are not derived. Consider this view:\n\nCREATE VIEW v AS SELECT col1, 1 AS col2 FROM t;\n\nThis view is not insertable because col2 is derived from an expression.\nBut it is updatable if the update does not try to update col2. This\nupdate is allowable:\n\nUPDATE v SET col1 = 0;\n\nThis update is not allowable because it attempts to update a derived\ncolumn:\n\nUPDATE v SET col2 = 0;\n\nIt is sometimes possible for a multiple-table view to be updatable,\nassuming that it can be processed with the MERGE algorithm. For this to\nwork, the view must use an inner join (not an outer join or a UNION).\nAlso, only a single table in the view definition can be updated, so the\nSET clause must name only columns from one of the tables in the view.\nViews that use UNION ALL are disallowed even though they might be\ntheoretically updatable, because the implementation uses temporary\ntables to process them.\n\nFor a multiple-table updatable view, INSERT can work if it inserts into\na single table. DELETE is not supported.\n\nThe WITH CHECK OPTION clause can be given for an updatable view to\nprevent inserts or updates to rows except those for which the WHERE\nclause in the select_statement is true.\n','','create-view'),(410,'TRIM',33,'Syntax:\nTRIM([{BOTH | LEADING | TRAILING} [remstr] FROM] str), TRIM(remstr\nFROM] str)\n\nReturns the string str with all remstr prefixes or suffixes removed. If\nnone of the specifiers BOTH, LEADING, or TRAILING is given, BOTH is\nassumed. remstr is optional and, if not specified, spaces are removed.\n','mysql> SELECT TRIM(\'  bar   \');\n        -> \'bar\'\nmysql> SELECT TRIM(LEADING \'x\' FROM \'xxxbarxxx\');\n        -> \'barxxx\'\nmysql> SELECT TRIM(BOTH \'x\' FROM \'xxxbarxxx\');\n        -> \'bar\'\nmysql> SELECT TRIM(TRAILING \'xyz\' FROM \'barxxyz\');\n        -> \'barx\'\n','string-functions'),(411,'IS',17,'Syntax:\nIS boolean_value, IS NOT boolean_value\n\nTests a value against a boolean value, where boolean_value can be TRUE,\nFALSE, or UNKNOWN.\n','mysql> SELECT 1 IS TRUE, 0 IS FALSE, NULL IS UNKNOWN;\n        -> 1, 1, 1\nmysql> SELECT 1 IS NOT UNKNOWN, 0 IS NOT UNKNOWN, NULL IS NOT UNKNOWN;\n        -> 1, 1, 0\n','comparison-operators'),(412,'GET_FORMAT',28,'Syntax:\nGET_FORMAT(DATE|TIME|DATETIME, \'EUR\'|\'USA\'|\'JIS\'|\'ISO\'|\'INTERNAL\')\n\nReturns a format string. This function is useful in combination with\nthe DATE_FORMAT() and the STR_TO_DATE() functions.\n','mysql> SELECT DATE_FORMAT(\'2003-10-03\',GET_FORMAT(DATE,\'EUR\'));\n        -> \'03.10.2003\'\nmysql> SELECT STR_TO_DATE(\'10.31.2003\',GET_FORMAT(DATE,\'USA\'));\n        -> \'2003-10-31\'\n','date-and-time-functions'),(413,'TINYBLOB',20,'TINYBLOB\n\nA BLOB column with a maximum length of 255 (28 - 1) bytes.\n','','string-type-overview'),(414,'SAVEPOINT',7,'Syntax:\nSAVEPOINT identifier\nROLLBACK [WORK] TO SAVEPOINT identifier\nRELEASE SAVEPOINT identifier\n\nInnoDB supports the SQL statements SAVEPOINT and ROLLBACK TO SAVEPOINT.\nStarting from MySQL 5.0.3, RELEASE SAVEPOINT and the optional WORK\nkeyword for ROLLBACK are supported as well.\n','','savepoints'),(415,'USER',15,'Syntax:\nUSER()\n\nReturns the current MySQL username and hostname as a string in the utf8\ncharacter set.\n','mysql> SELECT USER();\n        -> \'davida@localhost\'\n','information-functions'),(416,'MPOINTFROMWKB',29,'MPointFromWKB(wkb[,srid]), MultiPointFromWKB(wkb[,srid])\n\nConstructs a MULTIPOINT value using its WKB representation and SRID.\n','','gis-wkb-functions'),(417,'ALTER TABLE',36,'Syntax:\nALTER [IGNORE] TABLE tbl_name\n    alter_specification [, alter_specification] ...\n\nalter_specification:\n    ADD [COLUMN] column_definition [FIRST | AFTER col_name ]\n  | ADD [COLUMN] (column_definition,...)\n  | ADD INDEX [index_name] [index_type] (index_col_name,...)\n  | ADD [CONSTRAINT [symbol]]\n        PRIMARY KEY [index_type] (index_col_name,...)\n  | ADD [CONSTRAINT [symbol]]\n        UNIQUE [INDEX] [index_name] [index_type] (index_col_name,...)\n  | ADD [FULLTEXT|SPATIAL] [INDEX] [index_name] (index_col_name,...)\n  | ADD [CONSTRAINT [symbol]]\n        FOREIGN KEY [index_name] (index_col_name,...)\n        [reference_definition]\n  | ALTER [COLUMN] col_name {SET DEFAULT literal | DROP DEFAULT}\n  | CHANGE [COLUMN] old_col_name column_definition\n        [FIRST|AFTER col_name]\n  | MODIFY [COLUMN] column_definition [FIRST | AFTER col_name]\n  | DROP [COLUMN] col_name\n  | DROP PRIMARY KEY\n  | DROP INDEX index_name\n  | DROP FOREIGN KEY fk_symbol\n  | DISABLE KEYS\n  | ENABLE KEYS\n  | RENAME [TO] new_tbl_name\n  | ORDER BY col_name\n  | CONVERT TO CHARACTER SET charset_name [COLLATE collation_name]\n  | [DEFAULT] CHARACTER SET charset_name [COLLATE collation_name]\n  | DISCARD TABLESPACE\n  | IMPORT TABLESPACE\n  | table_options\n\nALTER TABLE enables you to change the structure of an existing table.\nFor example, you can add or delete columns, create or destroy indexes,\nchange the type of existing columns, or rename columns or the table\nitself. You can also change the comment for the table and type of the\ntable.\n','','alter-table'),(418,'PURGE MASTER LOGS',25,'Syntax:\nPURGE {MASTER | BINARY} LOGS TO \'log_name\'\nPURGE {MASTER | BINARY} LOGS BEFORE \'date\'\n\nDeletes all the binary logs listed in the log index prior to the\nspecified log or date. The logs also are removed from the list recorded\nin the log index file, so that the given log becomes the first.\n','PURGE MASTER LOGS TO \'mysql-bin.010\';\nPURGE MASTER LOGS BEFORE \'2003-04-02 22:46:26\';\n','purge-master-logs'),(419,'CHAR BYTE',20,'The CHAR BYTE data type is an alias for the BINARY type. This is a\ncompatibility feature.\n','','string-type-overview'),(420,'REPAIR TABLE',19,'Syntax:\nREPAIR [LOCAL | NO_WRITE_TO_BINLOG] TABLE\n    tbl_name [, tbl_name] ... [QUICK] [EXTENDED] [USE_FRM]\n\nREPAIR TABLE repairs a possibly corrupted table. By default, it has the\nsame effect as myisamchk --recover tbl_name. REPAIR TABLE works for\nMyISAM and for ARCHIVE tables. See [myisam-storage-engine], and\n[archive-storage-engine].\n','','repair-table'),(421,'MERGE',36,'The MERGE storage engine, also known as the MRG_MyISAM engine, is a\ncollection of identical MyISAM tables that can be used as one.\n\"Identical\" means that all tables have identical column and index\ninformation. You cannot merge MyISAM tables in which the columns are\nlisted in a different order, do not have exactly the same columns, or\nhave the indexes in different order. However, any or all of the MyISAM\ntables can be compressed with myisampack. See [myisampack]. Differences\nin table options such as AVG_ROW_LENGTH, MAX_ROWS, or PACK_KEYS do not\nmatter.\n','mysql> CREATE TABLE t1 (\n    ->    a INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n    ->    message CHAR(20)) ENGINE=MyISAM;\nmysql> CREATE TABLE t2 (\n    ->    a INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n    ->    message CHAR(20)) ENGINE=MyISAM;\nmysql> INSERT INTO t1 (message) VALUES (\'Testing\'),(\'table\'),(\'t1\');\nmysql> INSERT INTO t2 (message) VALUES (\'Testing\'),(\'table\'),(\'t2\');\nmysql> CREATE TABLE total (\n    ->    a INT NOT NULL AUTO_INCREMENT,\n    ->    message CHAR(20), INDEX(a))\n    ->    ENGINE=MERGE UNION=(t1,t2) INSERT_METHOD=LAST;\n','merge-storage-engine'),(422,'CREATE TABLE',36,'Syntax:\nCREATE [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name\n    [(create_definition,...)]\n    [table_options] [select_statement]\n\nOr:\n\nCREATE [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name\n    [(] LIKE old_tbl_name [)];\n\ncreate_definition:\n    column_definition\n  | [CONSTRAINT [symbol]] PRIMARY KEY [index_type] (index_col_name,...)\n  | KEY [index_name] [index_type] (index_col_name,...)\n  | INDEX [index_name] [index_type] (index_col_name,...)\n  | [CONSTRAINT [symbol]] UNIQUE [INDEX]\n        [index_name] [index_type] (index_col_name,...)\n  | [FULLTEXT|SPATIAL] [INDEX] [index_name] (index_col_name,...)\n  | [CONSTRAINT [symbol]] FOREIGN KEY\n        [index_name] (index_col_name,...) [reference_definition]\n  | CHECK (expr)\n\ncolumn_definition:\n    col_name type [NOT NULL | NULL] [DEFAULT default_value]\n        [AUTO_INCREMENT] [UNIQUE [KEY] | [PRIMARY] KEY]\n        [COMMENT \'string\'] [reference_definition]\n\ntype:\n    TINYINT[(length)] [UNSIGNED] [ZEROFILL]\n  | SMALLINT[(length)] [UNSIGNED] [ZEROFILL]\n  | MEDIUMINT[(length)] [UNSIGNED] [ZEROFILL]\n  | INT[(length)] [UNSIGNED] [ZEROFILL]\n  | INTEGER[(length)] [UNSIGNED] [ZEROFILL]\n  | BIGINT[(length)] [UNSIGNED] [ZEROFILL]\n  | REAL[(length,decimals)] [UNSIGNED] [ZEROFILL]\n  | DOUBLE[(length,decimals)] [UNSIGNED] [ZEROFILL]\n  | FLOAT[(length,decimals)] [UNSIGNED] [ZEROFILL]\n  | DECIMAL(length,decimals) [UNSIGNED] [ZEROFILL]\n  | NUMERIC(length,decimals) [UNSIGNED] [ZEROFILL]\n  | DATE\n  | TIME\n  | TIMESTAMP\n  | DATETIME\n  | YEAR\n  | CHAR(length) [BINARY | ASCII | UNICODE]\n  | VARCHAR(length) [BINARY]\n  | BINARY(length)\n  | VARBINARY(length)\n  | TINYBLOB\n  | BLOB\n  | MEDIUMBLOB\n  | LONGBLOB\n  | TINYTEXT [BINARY]\n  | TEXT [BINARY]\n  | MEDIUMTEXT [BINARY]\n  | LONGTEXT [BINARY]\n  | ENUM(value1,value2,value3,...)\n  | SET(value1,value2,value3,...)\n  | spatial_type\n\nindex_col_name:\n    col_name [(length)] [ASC | DESC]\n\nreference_definition:\n    REFERENCES tbl_name [(index_col_name,...)]\n               [MATCH FULL | MATCH PARTIAL | MATCH SIMPLE]\n               [ON DELETE reference_option]\n               [ON UPDATE reference_option]\n\nreference_option:\n    RESTRICT | CASCADE | SET NULL | NO ACTION\n\ntable_options: table_option [table_option] ...\n\ntable_option:\n    {ENGINE|TYPE} [=] engine_name\n  | AUTO_INCREMENT [=] value\n  | AVG_ROW_LENGTH [=] value\n  | [DEFAULT] CHARACTER SET charset_name [COLLATE collation_name]\n  | CHECKSUM [=] {0 | 1}\n  | COMMENT [=] \'string\'\n  | CONNECTION [=] \'connect_string\'\n  | MAX_ROWS [=] value\n  | MIN_ROWS [=] value\n  | PACK_KEYS [=] {0 | 1 | DEFAULT}\n  | PASSWORD [=] \'string\'\n  | DELAY_KEY_WRITE [=] {0 | 1}\n  | ROW_FORMAT [=] {DEFAULT|DYNAMIC|FIXED|COMPRESSED|REDUNDANT|COMPACT}\n  | UNION [=] (tbl_name[,tbl_name]...)\n  | INSERT_METHOD [=] { NO | FIRST | LAST }\n  | DATA DIRECTORY [=] \'absolute path to directory\'\n  | INDEX DIRECTORY [=] \'absolute path to directory\'\n\nselect_statement:\n    [IGNORE | REPLACE] [AS] SELECT ...   (Some legal select statement)\n\nCREATE TABLE creates a table with the given name. You must have the\nCREATE privilege for the table.\n\nRules for allowable table names are given in [legal-names]. By default,\nthe table is created in the default database. An error occurs if the\ntable exists, if there is no default database, or if the database does\nnot exist.\n','','create-table'),(423,'>',17,'Syntax:\n>\n\nGreater than:\n','mysql> SELECT 2 > 2;\n        -> 0\n','comparison-operators'),(424,'ANALYZE TABLE',19,'Syntax:\nANALYZE [LOCAL | NO_WRITE_TO_BINLOG] TABLE tbl_name [, tbl_name] ...\n\nANALYZE TABLE analyzes and stores the key distribution for a table.\nDuring the analysis, the table is locked with a read lock. This\nstatement works with MyISAM, BDB, and InnoDB tables. For MyISAM tables,\nthis statement is equivalent to using myisamchk --analyze.\n\nMySQL uses the stored key distribution to decide the order in which\ntables should be joined when you perform a join on something other than\na constant.\n','','analyze-table'),(425,'MICROSECOND',28,'Syntax:\nMICROSECOND(expr)\n\nReturns the microseconds from the time or datetime expression expr as a\nnumber in the range from 0 to 999999.\n','mysql> SELECT MICROSECOND(\'12:00:00.123456\');\n        -> 123456\nmysql> SELECT MICROSECOND(\'1997-12-31 23:59:59.000010\');\n        -> 10\n','date-and-time-functions'),(426,'CONSTRAINT',36,'InnoDB also supports foreign key constraints. The syntax for a foreign\nkey constraint definition in InnoDB looks like this:\n\n[CONSTRAINT symbol] FOREIGN KEY [id] (index_col_name, ...)\n    REFERENCES tbl_name (index_col_name, ...)\n    [ON DELETE {RESTRICT | CASCADE | SET NULL | NO ACTION}]\n    [ON UPDATE {RESTRICT | CASCADE | SET NULL | NO ACTION}]\n','CREATE TABLE product (category INT NOT NULL, id INT NOT NULL,\n                      price DECIMAL,\n                      PRIMARY KEY(category, id)) ENGINE=INNODB;\nCREATE TABLE customer (id INT NOT NULL,\n                       PRIMARY KEY (id)) ENGINE=INNODB;\nCREATE TABLE product_order (no INT NOT NULL AUTO_INCREMENT,\n                            product_category INT NOT NULL,\n                            product_id INT NOT NULL,\n                            customer_id INT NOT NULL,\n                            PRIMARY KEY(no),\n                            INDEX (product_category, product_id),\n                            FOREIGN KEY (product_category, product_id)\n                              REFERENCES product(category, id)\n                              ON UPDATE CASCADE ON DELETE RESTRICT,\n                            INDEX (customer_id),\n                            FOREIGN KEY (customer_id)\n                              REFERENCES customer(id)) ENGINE=INNODB;\n','innodb-foreign-key-constraints'),(427,'FIELD',33,'Syntax:\nFIELD(str,str1,str2,str3,...)\n\nReturns the index (position) of str in the str1, str2, str3, ... list.\nReturns 0 if str is not found.\n\nIf all arguments to FIELD() are strings, all arguments are compared as\nstrings. If all arguments are numbers, they are compared as numbers.\nOtherwise, the arguments are compared as double.\n\nIf str is NULL, the return value is 0 because NULL fails equality\ncomparison with any value. FIELD() is the complement of ELT().\n','mysql> SELECT FIELD(\'ej\', \'Hej\', \'ej\', \'Heja\', \'hej\', \'foo\');\n        -> 2\nmysql> SELECT FIELD(\'fo\', \'Hej\', \'ej\', \'Heja\', \'hej\', \'foo\');\n        -> 0\n','string-functions'),(428,'MAKETIME',28,'Syntax:\nMAKETIME(hour,minute,second)\n\nReturns a time value calculated from the hour, minute, and second\narguments.\n','mysql> SELECT MAKETIME(12,15,30);\n        -> \'12:15:30\'\n','date-and-time-functions'),(429,'CURDATE',28,'Syntax:\nCURDATE()\n\nReturns the current date as a value in \'YYYY-MM-DD\' or YYYYMMDD format,\ndepending on whether the function is used in a string or numeric\ncontext.\n','mysql> SELECT CURDATE();\n        -> \'1997-12-15\'\nmysql> SELECT CURDATE() + 0;\n        -> 19971215\n','date-and-time-functions'),(430,'MIN MAX',14,'Syntax:\nMIN([DISTINCT] expr), MAX([DISTINCT] expr)\n\nReturns the minimum or maximum value of expr. MIN() and MAX() may take\na string argument; in such cases they return the minimum or maximum\nstring value. See [mysql-indexes]. The DISTINCT keyword can be used to\nfind the minimum or maximum of the distinct values of expr, however,\nthis produces the same result as omitting DISTINCT.\n\nMIN() and MAX() return NULL if there were no matching rows.\n','mysql> SELECT student_name, MIN(test_score), MAX(test_score)\n    ->        FROM student\n    ->        GROUP BY student_name;\n','group-by-functions'),(431,'SET PASSWORD',8,'Syntax:\nSET PASSWORD [FOR user] = PASSWORD(\'some password\')\n\nThe SET PASSWORD statement assigns a password to an existing MySQL user\naccount.\n\nWith no FOR clause, this statement sets the password for the current\nuser. Any client that has connected to the server using a non-anonymous\naccount can change the password for that account.\n\nWith a FOR clause, this statement sets the password for a specific\naccount on the current server host. Only clients that have the UPDATE\nprivilege for the mysql database can do this. The user value should be\ngiven in user_name@host_name format, where user_name and host_name are\nexactly as they are listed in the User and Host columns of the\nmysql.user table entry. For example, if you had an entry with User and\nHost column values of \'bob\' and \'%.loc.gov\', you would write the\nstatement like this:\n\nSET PASSWORD FOR \'bob\'@\'%.loc.gov\' = PASSWORD(\'newpass\');\n','','set-password'),(432,'ENUM',20,'ENUM(\'value1\',\'value2\',...)\n\nAn enumeration. A string object that can have only one value, chosen\nfrom the list of values \'value1\', \'value2\', ..., NULL or the special \'\'\nerror value. An ENUM column can have a maximum of 65,535 distinct\nvalues. ENUM values are represented internally as integers.\n','','string-type-overview'),(433,'IF FUNCTION',6,'Syntax:\nIF(expr1,expr2,expr3)\n\nIf expr1 is TRUE (expr1 <> 0 and expr1 <> NULL) then IF() returns\nexpr2; otherwise it returns expr3. IF() returns a numeric or string\nvalue, depending on the context in which it is used.\n','mysql> SELECT IF(1>2,2,3);\n        -> 3\nmysql> SELECT IF(1<2,\'yes\',\'no\');\n        -> \'yes\'\nmysql> SELECT IF(STRCMP(\'test\',\'test1\'),\'no\',\'yes\');\n        -> \'no\'\n','control-flow-functions'),(434,'DATABASE',15,'Syntax:\nDATABASE()\n\nReturns the default (current) database name as a string in the utf8\ncharacter set. If there is no default database, DATABASE() returns\nNULL. Within a stored routine, the default database is the database\nthat the routine is associated with, which is not necessarily the same\nas the database that is the default in the calling context.\n','mysql> SELECT DATABASE();\n        -> \'test\'\n','information-functions'),(435,'POINTFROMWKB',29,'PointFromWKB(wkb[,srid])\n\nConstructs a POINT value using its WKB representation and SRID.\n','','gis-wkb-functions'),(436,'POWER',4,'Syntax:\nPOW(X,Y), POWER(X,Y)\n\nReturns the value of X raised to the power of Y.\n','mysql> SELECT POW(2,2);\n        -> 4\nmysql> SELECT POW(2,-2);\n        -> 0.25\n','mathematical-functions'),(437,'ATAN',4,'Syntax:\nATAN(X)\n\nReturns the arc tangent of X, that is, the value whose tangent is X.\n','mysql> SELECT ATAN(2);\n        -> 1.1071487177941\nmysql> SELECT ATAN(-2);\n        -> -1.1071487177941\n','mathematical-functions'),(438,'STRCMP',33,'Syntax:\nSTRCMP(expr1,expr2)\n\nSTRCMP() returns 0 if the strings are the same, -1 if the first\nargument is smaller than the second according to the current sort\norder, and 1 otherwise.\n','mysql> SELECT STRCMP(\'text\', \'text2\');\n        -> -1\nmysql> SELECT STRCMP(\'text2\', \'text\');\n        -> 1\nmysql> SELECT STRCMP(\'text\', \'text\');\n        -> 0\n','string-comparison-functions'),(439,'INSERT DELAYED',25,'Syntax:\nINSERT DELAYED ...\n\nThe DELAYED option for the INSERT statement is a MySQL extension to\nstandard SQL that is very useful if you have clients that cannot or\nneed not wait for the INSERT to complete. This is a common situation\nwhen you use MySQL for logging and you also periodically run SELECT and\nUPDATE statements that take a long time to complete.\n\nWhen a client uses INSERT DELAYED, it gets an okay from the server at\nonce, and the row is queued to be inserted when the table is not in use\nby any other thread.\n\nAnother major benefit of using INSERT DELAYED is that inserts from many\nclients are bundled together and written in one block. This is much\nfaster than performing many separate inserts.\n\nNote that INSERT DELAYED is slower than a normal INSERT if the table is\nnot otherwise in use. There is also the additional overhead for the\nserver to handle a separate thread for each table for which there are\ndelayed rows. This means that you should use INSERT DELAYED only when\nyou are really sure that you need it.\n\nThe queued rows are held only in memory until they are inserted into\nthe table. This means that if you terminate mysqld forcibly (for\nexample, with kill -9) or if mysqld dies unexpectedly, any queued rows\nthat have not been written to disk are lost.\n\nThere are some constraints on the use of DELAYED:\n\no INSERT DELAYED works only with MyISAM, MEMORY, and ARCHIVE tables.\n  See [myisam-storage-engine], [memory-storage-engine], and\n  [archive-storage-engine].\n\n  For MyISAM tables, if there are no free blocks in the middle of the\n  data file, concurrent SELECT and INSERT statements are supported.\n  Under these circumstances, you very seldom need to use INSERT DELAYED\n  with MyISAM.\n\no INSERT DELAYED should be used only for INSERT statements that specify\n  value lists. The server ignores DELAYED for INSERT ... SELECT or\n  INSERT ... ON DUPLICATE KEY UPDATE statements.\n\no Because the INSERT DELAYED statement returns immediately, before the\n  rows are inserted, you cannot use LAST_INSERT_ID() to get the\n  AUTO_INCREMENT value that the statement might generate.\n\no DELAYED rows are not visible to SELECT statements until they actually\n  have been inserted.\n\no DELAYED is ignored on slave replication servers because it could\n  cause the slave to have different data than the master.\n','','insert-delayed'),(440,'MEDIUMTEXT',20,'MEDIUMTEXT\n\nA TEXT column with a maximum length of 16,777,215 (224 - 1) characters.\n','','string-type-overview'),(441,'LN',4,'Syntax:\nLN(X)\n\nReturns the natural logarithm of X; that is, the base-e logarithm of X.\n','mysql> SELECT LN(2);\n        -> 0.69314718055995\nmysql> SELECT LN(-2);\n        -> NULL\n','mathematical-functions'),(442,'SHOW COLLATION',25,'Syntax:\nSHOW COLLATION [LIKE \'pattern\']\n\nThe output from SHOW COLLATION includes all available character sets.\nIt takes an optional LIKE clause whose pattern indicates which\ncollation names to match. For example:\n\nmysql> SHOW COLLATION LIKE \'latin1%\';\n+-------------------+---------+----+---------+----------+---------+\n| Collation         | Charset | Id | Default | Compiled | Sortlen |\n+-------------------+---------+----+---------+----------+---------+\n| latin1_german1_ci | latin1  |  5 |         |          |       0 |\n| latin1_swedish_ci | latin1  |  8 | Yes     | Yes      |       0 |\n| latin1_danish_ci  | latin1  | 15 |         |          |       0 |\n| latin1_german2_ci | latin1  | 31 |         | Yes      |       2 |\n| latin1_bin        | latin1  | 47 |         | Yes      |       0 |\n| latin1_general_ci | latin1  | 48 |         |          |       0 |\n| latin1_general_cs | latin1  | 49 |         |          |       0 |\n| latin1_spanish_ci | latin1  | 94 |         |          |       0 |\n+-------------------+---------+----+---------+----------+---------+\n','','show-collation'),(443,'LOG',4,'Syntax:\nLOG(X), LOG(B,X)\n\nIf called with one parameter, this function returns the natural\nlogarithm of X.\n','mysql> SELECT LOG(2);\n        -> 0.69314718055995\nmysql> SELECT LOG(-2);\n        -> NULL\n','mathematical-functions'),(444,'SET SQL_LOG_BIN',25,'Syntax:\nSET SQL_LOG_BIN = {0|1}\n\nDisables or enables binary logging for the current connection\n(SQL_LOG_BIN is a session variable) if the client has the SUPER\nprivilege. The statement is refused with an error if the client does\nnot have that privilege.\n','','set-sql-log-bin'),(445,'!=',17,'Syntax:\n<>, !=\n\nNot equal:\n','mysql> SELECT \'.01\' <> \'0.01\';\n        -> 1\nmysql> SELECT .01 <> \'0.01\';\n        -> 0\nmysql> SELECT \'zapp\' <> \'zappp\';\n        -> 1\n','comparison-operators'),(446,'WHILE',35,'Syntax:\n[begin_label:] WHILE search_condition DO\n    statement_list\nEND WHILE [end_label]\n\nThe statement list within a WHILE statement is repeated as long as the\nsearch_condition is true. statement_list consists of one or more\nstatements.\n\nA WHILE statement can be labeled. end_label cannot be given unless\nbegin_label also is present. If both are present, they must be the\nsame.\n','CREATE PROCEDURE dowhile()\nBEGIN\n  DECLARE v1 INT DEFAULT 5;\n\n  WHILE v1 > 0 DO\n    ...\n    SET v1 = v1 - 1;\n  END WHILE;\nEND\n','while-statement'),(447,'AES_DECRYPT',10,'Syntax:\nAES_ENCRYPT(str,key_str), AES_DECRYPT(crypt_str,key_str)\n\nThese functions allow encryption and decryption of data using the\nofficial AES (Advanced Encryption Standard) algorithm, previously known\nas \"Rijndael.\" Encoding with a 128-bit key length is used, but you can\nextend it up to 256 bits by modifying the source. We chose 128 bits\nbecause it is much faster and it is secure enough for most purposes.\n\nAES_ENCRYPT() encrypts a string and returns a binary string.\nAES_DESCRIPT() descrypts the encrypted string and returns the original\nstring. The input arguments may be any length. If either argument is\nNULL, the result of this function is also NULL.\n\nBecause AES is a block-level algorithm, padding is used to encode\nuneven length strings and so the result string length may be calculated\nusing this formula:\n\n16 Ã— (trunc(string_length / 16) + 1)\n\nIf AES_DECRYPT() detects invalid data or incorrect padding, it returns\nNULL. However, it is possible for AES_DECRYPT() to return a non-NULL\nvalue (possibly garbage) if the input data or the key is invalid.\n\nYou can use the AES functions to store data in an encrypted form by\nmodifying your queries:\n','INSERT INTO t VALUES (1,AES_ENCRYPT(\'text\',\'password\'));\n','encryption-functions'),(448,'DAYNAME',28,'Syntax:\nDAYNAME(date)\n\nReturns the name of the weekday for date.\n','mysql> SELECT DAYNAME(\'1998-02-05\');\n        -> \'Thursday\'\n','date-and-time-functions'),(449,'COERCIBILITY',15,'Syntax:\nCOERCIBILITY(str)\n\nReturns the collation coercibility value of the string argument.\n','mysql> SELECT COERCIBILITY(\'abc\' COLLATE latin1_swedish_ci);\n        -> 0\nmysql> SELECT COERCIBILITY(USER());\n        -> 3\nmysql> SELECT COERCIBILITY(\'abc\');\n        -> 4\n','information-functions'),(450,'INT',20,'INT[(M)] [UNSIGNED] [ZEROFILL]\n\nA normal-size integer. The signed range is -2147483648 to 2147483647.\nThe unsigned range is 0 to 4294967295.\n','','numeric-type-overview'),(451,'GLENGTH',11,'GLength(ls)\n\nReturns as a double-precision number the length of the LineString value\nls in its associated spatial reference.\n','mysql> SET @ls = \'LineString(1 1,2 2,3 3)\';\nmysql> SELECT GLength(GeomFromText(@ls));\n+----------------------------+\n| GLength(GeomFromText(@ls)) |\n+----------------------------+\n|            2.8284271247462 |\n+----------------------------+\n','linestring-property-functions'),(452,'RADIANS',4,'Syntax:\nRADIANS(X)\n\nReturns the argument X, converted from degrees to radians. (Note that\nÏ€ radians equals 180 degrees.)\n','mysql> SELECT RADIANS(90);\n        -> 1.5707963267949\n','mathematical-functions'),(453,'COLLATION',15,'Syntax:\nCOLLATION(str)\n\nReturns the collation of the string argument.\n','mysql> SELECT COLLATION(\'abc\');\n        -> \'latin1_swedish_ci\'\nmysql> SELECT COLLATION(_utf8\'abc\');\n        -> \'utf8_general_ci\'\n','information-functions'),(454,'COALESCE',17,'Syntax:\nCOALESCE(value,...)\n\nReturns the first non-NULL value in the list, or NULL if there are no\nnon-NULL values.\n','mysql> SELECT COALESCE(NULL,1);\n        -> 1\nmysql> SELECT COALESCE(NULL,NULL,NULL);\n        -> NULL\n','comparison-operators'),(455,'VERSION',15,'Syntax:\nVERSION()\n\nReturns a string that indicates the MySQL server version. The string\nuses the utf8 character set.\n','mysql> SELECT VERSION();\n        -> \'5.0.19-standard\'\n','information-functions'),(456,'MAKE_SET',33,'Syntax:\nMAKE_SET(bits,str1,str2,...)\n\nReturns a set value (a string containing substrings separated by `,\'\ncharacters) consisting of the strings that have the corresponding bit\nin bits set. str1 corresponds to bit 0, str2 to bit 1, and so on. NULL\nvalues in str1, str2, ... are not appended to the result.\n','mysql> SELECT MAKE_SET(1,\'a\',\'b\',\'c\');\n        -> \'a\'\nmysql> SELECT MAKE_SET(1 | 4,\'hello\',\'nice\',\'world\');\n        -> \'hello,world\'\nmysql> SELECT MAKE_SET(1 | 4,\'hello\',\'nice\',NULL,\'world\');\n        -> \'hello\'\nmysql> SELECT MAKE_SET(0,\'a\',\'b\',\'c\');\n        -> \'\'\n','string-functions'),(457,'FIND_IN_SET',33,'Syntax:\nFIND_IN_SET(str,strlist)\n\nReturns a value in the range of 1 to N if the string str is in the\nstring list strlist consisting of N substrings. A string list is a\nstring composed of substrings separated by `,\' characters. If the first\nargument is a constant string and the second is a column of type SET,\nthe FIND_IN_SET() function is optimized to use bit arithmetic. Returns\n0 if str is not in strlist or if strlist is the empty string. Returns\nNULL if either argument is NULL. This function does not work properly\nif the first argument contains a comma (`,\') character.\n','mysql> SELECT FIND_IN_SET(\'b\',\'a,b,c,d\');\n        -> 2\n','string-functions');
/*!40000 ALTER TABLE `help_topic` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `host`
--

DROP TABLE IF EXISTS `host`;
CREATE TABLE `host` (
  `Host` char(60) collate utf8_bin NOT NULL default '',
  `Db` char(64) collate utf8_bin NOT NULL default '',
  `Select_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Insert_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Update_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Delete_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Drop_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Grant_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `References_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Index_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Alter_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_tmp_table_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Lock_tables_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_view_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Show_view_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_routine_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Alter_routine_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Execute_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  PRIMARY KEY  (`Host`,`Db`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Host privileges;  Merged with database privileges';

--
-- Dumping data for table `host`
--

LOCK TABLES `host` WRITE;
/*!40000 ALTER TABLE `host` DISABLE KEYS */;
/*!40000 ALTER TABLE `host` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proc`
--

DROP TABLE IF EXISTS `proc`;
CREATE TABLE `proc` (
  `db` char(64) character set utf8 collate utf8_bin NOT NULL default '',
  `name` char(64) NOT NULL default '',
  `type` enum('FUNCTION','PROCEDURE') NOT NULL,
  `specific_name` char(64) NOT NULL default '',
  `language` enum('SQL') NOT NULL default 'SQL',
  `sql_data_access` enum('CONTAINS_SQL','NO_SQL','READS_SQL_DATA','MODIFIES_SQL_DATA') NOT NULL default 'CONTAINS_SQL',
  `is_deterministic` enum('YES','NO') NOT NULL default 'NO',
  `security_type` enum('INVOKER','DEFINER') NOT NULL default 'DEFINER',
  `param_list` blob NOT NULL,
  `returns` char(64) NOT NULL default '',
  `body` longblob NOT NULL,
  `definer` char(77) character set utf8 collate utf8_bin NOT NULL default '',
  `created` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `modified` timestamp NOT NULL default '0000-00-00 00:00:00',
  `sql_mode` set('REAL_AS_FLOAT','PIPES_AS_CONCAT','ANSI_QUOTES','IGNORE_SPACE','NOT_USED','ONLY_FULL_GROUP_BY','NO_UNSIGNED_SUBTRACTION','NO_DIR_IN_CREATE','POSTGRESQL','ORACLE','MSSQL','DB2','MAXDB','NO_KEY_OPTIONS','NO_TABLE_OPTIONS','NO_FIELD_OPTIONS','MYSQL323','MYSQL40','ANSI','NO_AUTO_VALUE_ON_ZERO','NO_BACKSLASH_ESCAPES','STRICT_TRANS_TABLES','STRICT_ALL_TABLES','NO_ZERO_IN_DATE','NO_ZERO_DATE','INVALID_DATES','ERROR_FOR_DIVISION_BY_ZERO','TRADITIONAL','NO_AUTO_CREATE_USER','HIGH_NOT_PRECEDENCE') NOT NULL default '',
  `comment` char(64) character set utf8 collate utf8_bin NOT NULL default '',
  PRIMARY KEY  (`db`,`name`,`type`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Stored Procedures';

--
-- Dumping data for table `proc`
--

LOCK TABLES `proc` WRITE;
/*!40000 ALTER TABLE `proc` DISABLE KEYS */;
/*!40000 ALTER TABLE `proc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `procs_priv`
--

DROP TABLE IF EXISTS `procs_priv`;
CREATE TABLE `procs_priv` (
  `Host` char(60) collate utf8_bin NOT NULL default '',
  `Db` char(64) collate utf8_bin NOT NULL default '',
  `User` char(16) collate utf8_bin NOT NULL default '',
  `Routine_name` char(64) collate utf8_bin NOT NULL default '',
  `Routine_type` enum('FUNCTION','PROCEDURE') collate utf8_bin NOT NULL,
  `Grantor` char(77) collate utf8_bin NOT NULL default '',
  `Proc_priv` set('Execute','Alter Routine','Grant') character set utf8 NOT NULL default '',
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`Host`,`Db`,`User`,`Routine_name`,`Routine_type`),
  KEY `Grantor` (`Grantor`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Procedure privileges';

--
-- Dumping data for table `procs_priv`
--

LOCK TABLES `procs_priv` WRITE;
/*!40000 ALTER TABLE `procs_priv` DISABLE KEYS */;
/*!40000 ALTER TABLE `procs_priv` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tables_priv`
--

DROP TABLE IF EXISTS `tables_priv`;
CREATE TABLE `tables_priv` (
  `Host` char(60) collate utf8_bin NOT NULL default '',
  `Db` char(64) collate utf8_bin NOT NULL default '',
  `User` char(16) collate utf8_bin NOT NULL default '',
  `Table_name` char(64) collate utf8_bin NOT NULL default '',
  `Grantor` char(77) collate utf8_bin NOT NULL default '',
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `Table_priv` set('Select','Insert','Update','Delete','Create','Drop','Grant','References','Index','Alter','Create View','Show view') character set utf8 NOT NULL default '',
  `Column_priv` set('Select','Insert','Update','References') character set utf8 NOT NULL default '',
  PRIMARY KEY  (`Host`,`Db`,`User`,`Table_name`),
  KEY `Grantor` (`Grantor`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Table privileges';

--
-- Dumping data for table `tables_priv`
--

LOCK TABLES `tables_priv` WRITE;
/*!40000 ALTER TABLE `tables_priv` DISABLE KEYS */;
/*!40000 ALTER TABLE `tables_priv` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `time_zone`
--

DROP TABLE IF EXISTS `time_zone`;
CREATE TABLE `time_zone` (
  `Time_zone_id` int(10) unsigned NOT NULL auto_increment,
  `Use_leap_seconds` enum('Y','N') NOT NULL default 'N',
  PRIMARY KEY  (`Time_zone_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Time zones';

--
-- Dumping data for table `time_zone`
--

LOCK TABLES `time_zone` WRITE;
/*!40000 ALTER TABLE `time_zone` DISABLE KEYS */;
/*!40000 ALTER TABLE `time_zone` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `time_zone_leap_second`
--

DROP TABLE IF EXISTS `time_zone_leap_second`;
CREATE TABLE `time_zone_leap_second` (
  `Transition_time` bigint(20) NOT NULL,
  `Correction` int(11) NOT NULL,
  PRIMARY KEY  (`Transition_time`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Leap seconds information for time zones';

--
-- Dumping data for table `time_zone_leap_second`
--

LOCK TABLES `time_zone_leap_second` WRITE;
/*!40000 ALTER TABLE `time_zone_leap_second` DISABLE KEYS */;
/*!40000 ALTER TABLE `time_zone_leap_second` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `time_zone_name`
--

DROP TABLE IF EXISTS `time_zone_name`;
CREATE TABLE `time_zone_name` (
  `Name` char(64) NOT NULL,
  `Time_zone_id` int(10) unsigned NOT NULL,
  PRIMARY KEY  (`Name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Time zone names';

--
-- Dumping data for table `time_zone_name`
--

LOCK TABLES `time_zone_name` WRITE;
/*!40000 ALTER TABLE `time_zone_name` DISABLE KEYS */;
/*!40000 ALTER TABLE `time_zone_name` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `time_zone_transition`
--

DROP TABLE IF EXISTS `time_zone_transition`;
CREATE TABLE `time_zone_transition` (
  `Time_zone_id` int(10) unsigned NOT NULL,
  `Transition_time` bigint(20) NOT NULL,
  `Transition_type_id` int(10) unsigned NOT NULL,
  PRIMARY KEY  (`Time_zone_id`,`Transition_time`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Time zone transitions';

--
-- Dumping data for table `time_zone_transition`
--

LOCK TABLES `time_zone_transition` WRITE;
/*!40000 ALTER TABLE `time_zone_transition` DISABLE KEYS */;
/*!40000 ALTER TABLE `time_zone_transition` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `time_zone_transition_type`
--

DROP TABLE IF EXISTS `time_zone_transition_type`;
CREATE TABLE `time_zone_transition_type` (
  `Time_zone_id` int(10) unsigned NOT NULL,
  `Transition_type_id` int(10) unsigned NOT NULL,
  `Offset` int(11) NOT NULL default '0',
  `Is_DST` tinyint(3) unsigned NOT NULL default '0',
  `Abbreviation` char(8) NOT NULL default '',
  PRIMARY KEY  (`Time_zone_id`,`Transition_type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Time zone transition types';

--
-- Dumping data for table `time_zone_transition_type`
--

LOCK TABLES `time_zone_transition_type` WRITE;
/*!40000 ALTER TABLE `time_zone_transition_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `time_zone_transition_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `Host` char(60) collate utf8_bin NOT NULL default '',
  `User` char(16) collate utf8_bin NOT NULL default '',
  `Password` char(41) character set latin1 collate latin1_bin NOT NULL default '',
  `Select_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Insert_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Update_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Delete_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Drop_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Reload_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Shutdown_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Process_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `File_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Grant_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `References_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Index_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Alter_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Show_db_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Super_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_tmp_table_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Lock_tables_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Execute_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Repl_slave_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Repl_client_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_view_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Show_view_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_routine_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Alter_routine_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `Create_user_priv` enum('N','Y') character set utf8 NOT NULL default 'N',
  `ssl_type` enum('','ANY','X509','SPECIFIED') character set utf8 NOT NULL default '',
  `ssl_cipher` blob NOT NULL,
  `x509_issuer` blob NOT NULL,
  `x509_subject` blob NOT NULL,
  `max_questions` int(11) unsigned NOT NULL default '0',
  `max_updates` int(11) unsigned NOT NULL default '0',
  `max_connections` int(11) unsigned NOT NULL default '0',
  `max_user_connections` int(11) unsigned NOT NULL default '0',
  PRIMARY KEY  (`Host`,`User`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Users and global privileges';

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES ('%','root','','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','','','','',0,0,0,0);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `zkeco_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `zkeco_db` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `zkeco_db`;

--
-- Table structure for table `acc_antiback`
--

DROP TABLE IF EXISTS `acc_antiback`;
CREATE TABLE `acc_antiback` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `one_mode` tinyint(1) NOT NULL,
  `two_mode` tinyint(1) NOT NULL,
  `three_mode` tinyint(1) NOT NULL,
  `four_mode` tinyint(1) NOT NULL,
  `five_mode` tinyint(1) NOT NULL,
  `six_mode` tinyint(1) NOT NULL,
  `seven_mode` tinyint(1) NOT NULL,
  `eight_mode` tinyint(1) NOT NULL,
  `nine_mode` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_antiback_device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_antiback`
--

LOCK TABLES `acc_antiback` WRITE;
/*!40000 ALTER TABLE `acc_antiback` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_antiback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_auxiliary`
--

DROP TABLE IF EXISTS `acc_auxiliary`;
CREATE TABLE `acc_auxiliary` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `aux_no` smallint(5) unsigned default NULL,
  `printer_number` varchar(30) default NULL,
  `aux_name` varchar(30) default NULL,
  `aux_state` smallint(6) default NULL,
  `time_zone_status` smallint(6) default NULL,
  `time_zone_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_auxiliary_device_id` (`device_id`),
  KEY `acc_auxiliary_time_zone_id` (`time_zone_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_auxiliary`
--

LOCK TABLES `acc_auxiliary` WRITE;
/*!40000 ALTER TABLE `acc_auxiliary` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_auxiliary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_device`
--

DROP TABLE IF EXISTS `acc_device`;
CREATE TABLE `acc_device` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `door_count` int(11) default NULL,
  `reader_count` int(11) default NULL,
  `aux_in_count` int(11) default NULL,
  `aux_out_count` int(11) default NULL,
  `machine_type` int(11) default NULL,
  `IsOnlyRFMachine` int(11) default NULL,
  `iclock_server_on` tinyint(1) NOT NULL,
  `global_apb_on` tinyint(1) NOT NULL,
  `rexinput_fun_on` tinyint(1) NOT NULL,
  `card_format_fun_on` tinyint(1) NOT NULL,
  `super_auth_fun_on` tinyint(1) NOT NULL,
  `time_apb_fun_on` tinyint(1) NOT NULL,
  `reader_cfg_fun_on` tinyint(1) NOT NULL,
  `reader_linkage_fun_on` tinyint(1) NOT NULL,
  `relay_state_fun_on` tinyint(1) NOT NULL,
  `ext_485_reader_fun_on` tinyint(1) NOT NULL,
  `ctl_all_relay_fun_on` tinyint(1) NOT NULL,
  `loss_card_fun_on` tinyint(1) NOT NULL,
  `aux_in_monitor_fun_on` tinyint(1) NOT NULL,
  `aux_out_tz_fun_on` tinyint(1) NOT NULL,
  `user_type_fun_on` tinyint(1) NOT NULL,
  `dst_fun_on` tinyint(1) NOT NULL,
  `auto_wgfmt_fun_on` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_device`
--

LOCK TABLES `acc_device` WRITE;
/*!40000 ALTER TABLE `acc_device` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_device` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_door`
--

DROP TABLE IF EXISTS `acc_door`;
CREATE TABLE `acc_door` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `door_no` smallint(5) unsigned default NULL,
  `door_name` varchar(30) default NULL,
  `lock_delay` smallint(5) unsigned default NULL,
  `back_lock` tinyint(1) NOT NULL,
  `sensor_delay` smallint(5) unsigned default NULL,
  `opendoor_type` smallint(6) default NULL,
  `inout_state` smallint(6) default NULL,
  `lock_active_id` int(11) default NULL,
  `long_open_id` int(11) default NULL,
  `wiegand_fmt_id` int(11) default NULL,
  `card_intervaltime` smallint(5) unsigned default NULL,
  `reader_type` smallint(6) default NULL,
  `is_att` tinyint(1) NOT NULL,
  `force_pwd` varchar(18) default NULL,
  `supper_pwd` varchar(18) default NULL,
  `door_sensor_status` smallint(6) default NULL,
  `map_id` int(11) default NULL,
  `duration_apb` smallint(5) unsigned default NULL,
  `global_apb` tinyint(1) NOT NULL,
  `relay_reverse_status` smallint(6) default NULL,
  `latch_door_type` smallint(6) default NULL,
  `latch_time_out` smallint(5) unsigned default NULL,
  `enabled` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_door_device_id` (`device_id`),
  KEY `acc_door_lock_active_id` (`lock_active_id`),
  KEY `acc_door_long_open_id` (`long_open_id`),
  KEY `acc_door_wiegand_fmt_id` (`wiegand_fmt_id`),
  KEY `acc_door_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_door`
--

LOCK TABLES `acc_door` WRITE;
/*!40000 ALTER TABLE `acc_door` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_door` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_email`
--

DROP TABLE IF EXISTS `acc_email`;
CREATE TABLE `acc_email` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `sender` varchar(30) default NULL,
  `receiver` longtext,
  `content` longtext,
  `attachments` varchar(200) default NULL,
  `time` datetime default NULL,
  `event_type` smallint(6) default NULL,
  `send_ret` smallint(6) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_email`
--

LOCK TABLES `acc_email` WRITE;
/*!40000 ALTER TABLE `acc_email` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_email` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_firstopen`
--

DROP TABLE IF EXISTS `acc_firstopen`;
CREATE TABLE `acc_firstopen` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `door_id` int(11) default NULL,
  `timeseg_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_firstopen_door_id` (`door_id`),
  KEY `acc_firstopen_timeseg_id` (`timeseg_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_firstopen`
--

LOCK TABLES `acc_firstopen` WRITE;
/*!40000 ALTER TABLE `acc_firstopen` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_firstopen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_firstopen_emp`
--

DROP TABLE IF EXISTS `acc_firstopen_emp`;
CREATE TABLE `acc_firstopen_emp` (
  `id` int(11) NOT NULL auto_increment,
  `accfirstopen_id` int(11) NOT NULL,
  `employee_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `accfirstopen_id` (`accfirstopen_id`,`employee_id`),
  KEY `acc_firstopen_emp_accfirstopen_id` (`accfirstopen_id`),
  KEY `acc_firstopen_emp_employee_id` (`employee_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_firstopen_emp`
--

LOCK TABLES `acc_firstopen_emp` WRITE;
/*!40000 ALTER TABLE `acc_firstopen_emp` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_firstopen_emp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_global_apb`
--

DROP TABLE IF EXISTS `acc_global_apb`;
CREATE TABLE `acc_global_apb` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(30) default NULL,
  `timeseg_id` int(11) default NULL,
  `group_1_id` int(11) default NULL,
  `group_2_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `acc_global_apb_timeseg_id` (`timeseg_id`),
  KEY `acc_global_apb_group_1_id` (`group_1_id`),
  KEY `acc_global_apb_group_2_id` (`group_2_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_global_apb`
--

LOCK TABLES `acc_global_apb` WRITE;
/*!40000 ALTER TABLE `acc_global_apb` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_global_apb` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_global_apb_group`
--

DROP TABLE IF EXISTS `acc_global_apb_group`;
CREATE TABLE `acc_global_apb_group` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(30) default NULL,
  `memo` varchar(70) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_global_apb_group`
--

LOCK TABLES `acc_global_apb_group` WRITE;
/*!40000 ALTER TABLE `acc_global_apb_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_global_apb_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_holidays`
--

DROP TABLE IF EXISTS `acc_holidays`;
CREATE TABLE `acc_holidays` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `holiday_name` varchar(30) default NULL,
  `holiday_type` smallint(6) default NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `loop_by_year` smallint(6) default NULL,
  `memo` varchar(70) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `holiday_name` (`holiday_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_holidays`
--

LOCK TABLES `acc_holidays` WRITE;
/*!40000 ALTER TABLE `acc_holidays` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_holidays` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_interlock`
--

DROP TABLE IF EXISTS `acc_interlock`;
CREATE TABLE `acc_interlock` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `one_mode` tinyint(1) NOT NULL,
  `two_mode` tinyint(1) NOT NULL,
  `three_mode` tinyint(1) NOT NULL,
  `four_mode` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_interlock`
--

LOCK TABLES `acc_interlock` WRITE;
/*!40000 ALTER TABLE `acc_interlock` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_interlock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_levelset`
--

DROP TABLE IF EXISTS `acc_levelset`;
CREATE TABLE `acc_levelset` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `level_name` varchar(30) default NULL,
  `level_timeseg_id` int(11) default NULL,
  `level_type` int(11) default NULL,
  `is_visitor` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `level_name` (`level_name`),
  KEY `acc_levelset_level_timeseg_id` (`level_timeseg_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_levelset`
--

LOCK TABLES `acc_levelset` WRITE;
/*!40000 ALTER TABLE `acc_levelset` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_levelset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_levelset_door_group`
--

DROP TABLE IF EXISTS `acc_levelset_door_group`;
CREATE TABLE `acc_levelset_door_group` (
  `id` int(11) NOT NULL auto_increment,
  `acclevelset_id` int(11) NOT NULL,
  `accdoor_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `acclevelset_id` (`acclevelset_id`,`accdoor_id`),
  KEY `acc_levelset_door_group_acclevelset_id` (`acclevelset_id`),
  KEY `acc_levelset_door_group_accdoor_id` (`accdoor_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_levelset_door_group`
--

LOCK TABLES `acc_levelset_door_group` WRITE;
/*!40000 ALTER TABLE `acc_levelset_door_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_levelset_door_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_levelset_emp`
--

DROP TABLE IF EXISTS `acc_levelset_emp`;
CREATE TABLE `acc_levelset_emp` (
  `id` int(11) NOT NULL auto_increment,
  `acclevelset_id` int(11) NOT NULL,
  `employee_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `acclevelset_id` (`acclevelset_id`,`employee_id`),
  KEY `acc_levelset_emp_acclevelset_id` (`acclevelset_id`),
  KEY `acc_levelset_emp_employee_id` (`employee_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_levelset_emp`
--

LOCK TABLES `acc_levelset_emp` WRITE;
/*!40000 ALTER TABLE `acc_levelset_emp` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_levelset_emp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_linkageio`
--

DROP TABLE IF EXISTS `acc_linkageio`;
CREATE TABLE `acc_linkageio` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `linkage_name` varchar(30) NOT NULL,
  `device_id` int(11) default NULL,
  `trigger_opt` smallint(6) default NULL,
  `in_address_hide` smallint(6) default NULL,
  `in_address` smallint(6) default NULL,
  `out_type_hide` smallint(6) default NULL,
  `out_address_hide` smallint(6) default NULL,
  `out_address` smallint(6) default NULL,
  `action_type` smallint(6) default NULL,
  `delay_time` smallint(5) unsigned default NULL,
  `video_linkageio_state` varchar(10) NOT NULL,
  `video_linkageio_time` int(11) default NULL,
  `video_linkageio_record_time` int(11) default NULL,
  `email_address` longtext,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `linkage_name` (`linkage_name`),
  KEY `acc_linkageio_device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_linkageio`
--

LOCK TABLES `acc_linkageio` WRITE;
/*!40000 ALTER TABLE `acc_linkageio` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_linkageio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_map`
--

DROP TABLE IF EXISTS `acc_map`;
CREATE TABLE `acc_map` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `map_name` varchar(30) default NULL,
  `map_path` varchar(30) default NULL,
  `area_id` int(11) default NULL,
  `width` double default NULL,
  `height` double default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `map_name` (`map_name`),
  KEY `acc_map_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_map`
--

LOCK TABLES `acc_map` WRITE;
/*!40000 ALTER TABLE `acc_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_mapdoorpos`
--

DROP TABLE IF EXISTS `acc_mapdoorpos`;
CREATE TABLE `acc_mapdoorpos` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `map_door_id` int(11) default NULL,
  `map_id` int(11) default NULL,
  `width` double default NULL,
  `left` double default NULL,
  `top` double default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_mapdoorpos_map_door_id` (`map_door_id`),
  KEY `acc_mapdoorpos_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_mapdoorpos`
--

LOCK TABLES `acc_mapdoorpos` WRITE;
/*!40000 ALTER TABLE `acc_mapdoorpos` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_mapdoorpos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_monitor_log`
--

DROP TABLE IF EXISTS `acc_monitor_log`;
CREATE TABLE `acc_monitor_log` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `log_tag` int(11) default NULL,
  `time` datetime default NULL,
  `pin` varchar(20) default NULL,
  `card_no` varchar(20) default NULL,
  `device_id` int(11) default NULL,
  `device_sn` varchar(20) NOT NULL,
  `device_name` varchar(20) default NULL,
  `verified` int(11) default NULL,
  `state` int(11) default NULL,
  `state_name` varchar(30) default NULL,
  `event_type` smallint(6) default NULL,
  `trigger_opt` smallint(6) default NULL,
  `event_point_type` smallint(6) default NULL,
  `event_point_id` int(11) default NULL,
  `event_point_name` varchar(50) default NULL,
  `description` longtext,
  `firstname` varchar(24) default NULL,
  `lastname` varchar(20) default NULL,
  `dept` varchar(100) default NULL,
  `area` varchar(30) default NULL,
  `video_ip` varchar(40) default NULL,
  `channel_no` varchar(10) default NULL,
  `vid_record_path_name` varchar(200) default NULL,
  `vid_record_state` smallint(6) default NULL,
  `vid_capture_path_name` varchar(200) default NULL,
  `vid_capture_state` smallint(6) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `time` (`time`,`pin`,`card_no`,`device_id`,`verified`,`state`,`event_type`,`event_point_type`,`event_point_id`,`trigger_opt`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_monitor_log`
--

LOCK TABLES `acc_monitor_log` WRITE;
/*!40000 ALTER TABLE `acc_monitor_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_monitor_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_morecardempgroup`
--

DROP TABLE IF EXISTS `acc_morecardempgroup`;
CREATE TABLE `acc_morecardempgroup` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `group_name` varchar(30) NOT NULL,
  `memo` varchar(70) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `group_name` (`group_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_morecardempgroup`
--

LOCK TABLES `acc_morecardempgroup` WRITE;
/*!40000 ALTER TABLE `acc_morecardempgroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_morecardempgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_morecardgroup`
--

DROP TABLE IF EXISTS `acc_morecardgroup`;
CREATE TABLE `acc_morecardgroup` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `comb_id` int(11) default NULL,
  `group_id` int(11) default NULL,
  `opener_number` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_morecardgroup_comb_id` (`comb_id`),
  KEY `acc_morecardgroup_group_id` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_morecardgroup`
--

LOCK TABLES `acc_morecardgroup` WRITE;
/*!40000 ALTER TABLE `acc_morecardgroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_morecardgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_morecardset`
--

DROP TABLE IF EXISTS `acc_morecardset`;
CREATE TABLE `acc_morecardset` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `door_id` int(11) default NULL,
  `comb_name` varchar(30) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `comb_name` (`comb_name`),
  KEY `acc_morecardset_door_id` (`door_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_morecardset`
--

LOCK TABLES `acc_morecardset` WRITE;
/*!40000 ALTER TABLE `acc_morecardset` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_morecardset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_reader`
--

DROP TABLE IF EXISTS `acc_reader`;
CREATE TABLE `acc_reader` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `door_id` int(11) default NULL,
  `reader_no` smallint(5) unsigned default NULL,
  `reader_name` varchar(30) default NULL,
  `reader_state` smallint(6) default NULL,
  `global_apb_group_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_reader_door_id` (`door_id`),
  KEY `acc_reader_global_apb_group_id` (`global_apb_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_reader`
--

LOCK TABLES `acc_reader` WRITE;
/*!40000 ALTER TABLE `acc_reader` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_reader` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_timeseg`
--

DROP TABLE IF EXISTS `acc_timeseg`;
CREATE TABLE `acc_timeseg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `timeseg_name` varchar(30) NOT NULL,
  `memo` varchar(70) default NULL,
  `sunday_start1` time NOT NULL,
  `sunday_end1` time NOT NULL,
  `sunday_start2` time NOT NULL,
  `sunday_end2` time NOT NULL,
  `sunday_start3` time NOT NULL,
  `sunday_end3` time NOT NULL,
  `monday_start1` time NOT NULL,
  `monday_end1` time NOT NULL,
  `monday_start2` time NOT NULL,
  `monday_end2` time NOT NULL,
  `monday_start3` time NOT NULL,
  `monday_end3` time NOT NULL,
  `tuesday_start1` time NOT NULL,
  `tuesday_end1` time NOT NULL,
  `tuesday_start2` time NOT NULL,
  `tuesday_end2` time NOT NULL,
  `tuesday_start3` time NOT NULL,
  `tuesday_end3` time NOT NULL,
  `wednesday_start1` time NOT NULL,
  `wednesday_end1` time NOT NULL,
  `wednesday_start2` time NOT NULL,
  `wednesday_end2` time NOT NULL,
  `wednesday_start3` time NOT NULL,
  `wednesday_end3` time NOT NULL,
  `thursday_start1` time NOT NULL,
  `thursday_end1` time NOT NULL,
  `thursday_start2` time NOT NULL,
  `thursday_end2` time NOT NULL,
  `thursday_start3` time NOT NULL,
  `thursday_end3` time NOT NULL,
  `friday_start1` time NOT NULL,
  `friday_end1` time NOT NULL,
  `friday_start2` time NOT NULL,
  `friday_end2` time NOT NULL,
  `friday_start3` time NOT NULL,
  `friday_end3` time NOT NULL,
  `saturday_start1` time NOT NULL,
  `saturday_end1` time NOT NULL,
  `saturday_start2` time NOT NULL,
  `saturday_end2` time NOT NULL,
  `saturday_start3` time NOT NULL,
  `saturday_end3` time NOT NULL,
  `holidaytype1_start1` time NOT NULL,
  `holidaytype1_end1` time NOT NULL,
  `holidaytype1_start2` time NOT NULL,
  `holidaytype1_end2` time NOT NULL,
  `holidaytype1_start3` time NOT NULL,
  `holidaytype1_end3` time NOT NULL,
  `holidaytype2_start1` time NOT NULL,
  `holidaytype2_end1` time NOT NULL,
  `holidaytype2_start2` time NOT NULL,
  `holidaytype2_end2` time NOT NULL,
  `holidaytype2_start3` time NOT NULL,
  `holidaytype2_end3` time NOT NULL,
  `holidaytype3_start1` time NOT NULL,
  `holidaytype3_end1` time NOT NULL,
  `holidaytype3_start2` time NOT NULL,
  `holidaytype3_end2` time NOT NULL,
  `holidaytype3_start3` time NOT NULL,
  `holidaytype3_end3` time NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `timeseg_name` (`timeseg_name`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_timeseg`
--

LOCK TABLES `acc_timeseg` WRITE;
/*!40000 ALTER TABLE `acc_timeseg` DISABLE KEYS */;
INSERT INTO `acc_timeseg` VALUES (1,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'24-Hour Accessible','24-Hour Accessible','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00');
/*!40000 ALTER TABLE `acc_timeseg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_wiegandfmt`
--

DROP TABLE IF EXISTS `acc_wiegandfmt`;
CREATE TABLE `acc_wiegandfmt` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `wiegand_name` varchar(30) NOT NULL,
  `wiegand_count` int(11) default NULL,
  `wiegand_mode` smallint(6) NOT NULL,
  `odd_parity_start` smallint(6) default NULL,
  `odd_parity_count` smallint(6) default NULL,
  `even_parity_start` smallint(6) default NULL,
  `even_parity_count` smallint(6) default NULL,
  `cid_start` smallint(6) default NULL,
  `cid_count` smallint(6) default NULL,
  `facility_code_start` smallint(6) default NULL,
  `facility_code_count` smallint(6) default NULL,
  `site_code_start` smallint(6) default NULL,
  `site_code_count` smallint(6) default NULL,
  `manufactory_code_start` smallint(6) default NULL,
  `manufactory_code_count` smallint(6) default NULL,
  `first_p` smallint(6) default NULL,
  `second_p` smallint(6) default NULL,
  `before_fmt` varchar(80) default NULL,
  `after_fmt` varchar(80) default NULL,
  `default_fmt` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_wiegandfmt`
--

LOCK TABLES `acc_wiegandfmt` WRITE;
/*!40000 ALTER TABLE `acc_wiegandfmt` DISABLE KEYS */;
INSERT INTO `acc_wiegandfmt` VALUES (1,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Auto',NULL,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0),(2,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 26',26,1,14,13,1,13,2,24,0,0,0,0,0,0,1,26,'pccccccccccccccccccccccccp','eeeeeeeeeeeeeooooooooooooo',1),(3,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 26a',26,1,14,13,1,13,10,16,2,8,0,0,0,0,1,26,'pffffffffccccccccccccccccp','eeeeeeeeeeeeeooooooooooooo',0),(4,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 34',34,1,18,17,1,17,2,32,0,0,0,0,0,0,1,34,'pccccccccccccccccccccccccccccccccp','eeeeeeeeeeeeeeeeeooooooooooooooooo',1),(5,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 34a',34,1,18,17,1,17,18,16,0,0,2,16,0,0,1,34,'pssssssssssssssssccccccccccccccccp','eeeeeeeeeeeeeeeeeooooooooooooooooo',0),(6,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 36',36,1,1,15,16,21,18,18,0,0,2,16,0,0,1,36,'pssssssssssssssssccccccccccccccccccp','oooooooooooooooeeeeeeeeeeeeeeeeeeeee',1),(7,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 37',37,1,19,19,1,18,21,16,5,10,15,6,2,3,1,37,'pmmmffffffffffssssssccccccccccccccccp','eeeeeeeeeeeeeeeeeeooooooooooooooooooo',1),(8,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 37a',37,1,19,19,1,18,18,19,0,0,6,12,2,4,1,37,'pmmmmsssssssssssscccccccccccccccccccp','eeeeeeeeeeeeeeeeeeooooooooooooooooooo',0),(9,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 50',50,1,26,25,1,25,18,32,0,0,2,16,0,0,1,50,'pssssssssssssssssccccccccccccccccccccccccccccccccp','eeeeeeeeeeeeeeeeeeeeeeeeeooooooooooooooooooooooooo',1),(10,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 66',66,1,34,33,1,33,2,64,0,0,0,0,0,0,1,66,'pccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccp','eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeooooooooooooooooooooooooooooooooo',1),(11,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 35',35,1,19,17,1,18,15,20,0,0,2,13,0,0,1,35,'psssssssssssssccccccccccccccccccccp','eeeeeeeeeeeeeeeeeeooooooooooooooooo',1);
/*!40000 ALTER TABLE `acc_wiegandfmt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `action_log`
--

DROP TABLE IF EXISTS `action_log`;
CREATE TABLE `action_log` (
  `id` int(11) NOT NULL auto_increment,
  `action_time` datetime NOT NULL,
  `user_id` int(11) default NULL,
  `content_type_id` int(11) default NULL,
  `object_id` varchar(100) default NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` varchar(512) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `action_log_user_id` (`user_id`),
  KEY `action_log_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=94 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `action_log`
--

LOCK TABLES `action_log` WRITE;
/*!40000 ALTER TABLE `action_log` DISABLE KEYS */;
INSERT INTO `action_log` VALUES (1,'2025-10-06 15:12:43',NULL,15,'1','company(Company Name)',1,''),(2,'2025-10-06 15:12:43',NULL,15,'2','dbversion(5.31)',1,''),(3,'2025-10-06 15:12:43',NULL,15,'3','date_format(%m/%d/%Y)',1,''),(4,'2025-10-06 15:12:43',NULL,15,'4','browse_title(Access Control System)',1,''),(5,'2025-10-06 15:12:43',NULL,13,'1','System.Date Format',1,''),(6,'2025-10-06 15:12:43',NULL,13,'2','System.Time Format',1,''),(7,'2025-10-06 15:12:43',NULL,13,'3','System.Datetime Format',1,''),(8,'2025-10-06 15:12:43',NULL,13,'4','System.Shortdate format',1,''),(9,'2025-10-06 15:12:43',NULL,13,'5','System.Shortdatetime Format',1,''),(10,'2025-10-06 15:12:43',NULL,13,'6','System.Language',1,''),(11,'2025-10-06 15:12:43',NULL,13,'7','System.System Default Page',1,''),(12,'2025-10-06 15:12:43',NULL,13,'8','System.System Default Page',1,''),(13,'2025-10-06 15:12:43',NULL,13,'9','System.Device List Page',1,''),(14,'2025-10-06 15:12:43',NULL,13,'10','System.Backup Time',1,''),(15,'2025-10-06 15:12:43',NULL,13,'11','dbapp.Maximum Image Width',1,''),(16,'2025-10-06 15:12:43',NULL,13,'12','dbapp.Style',1,''),(17,'2025-10-06 15:12:43',NULL,22,'1','1 Area Name',1,''),(18,'2025-10-06 15:12:43',NULL,26,'1','01 VIP card',1,''),(19,'2025-10-06 15:12:43',NULL,26,'2','02 Ordinary card',1,''),(20,'2025-10-06 15:12:43',NULL,20,'1','1 Department Name',1,''),(21,'2025-10-06 15:12:43',NULL,54,'CompanyLogo','CompanyLogo',1,''),(22,'2025-10-06 15:12:43',NULL,13,'13','Personnel.Default access control page',1,''),(23,'2025-10-06 15:12:43',NULL,29,'1','System',1,''),(24,'2025-10-06 15:12:43',NULL,29,'2','Attendance',1,''),(25,'2025-10-06 15:12:43',NULL,29,'3','Access Control',1,''),(26,'2025-10-06 15:12:43',NULL,29,'4','Personnel',1,''),(27,'2025-10-06 15:12:44',NULL,13,'14','Device.Default access control page',1,''),(28,'2025-10-06 15:12:44',NULL,45,'1','New Year’s Day',1,''),(29,'2025-10-06 15:12:44',NULL,45,'2','National Day',1,''),(30,'2025-10-06 15:12:44',NULL,51,'1','Sick',1,''),(31,'2025-10-06 15:12:44',NULL,51,'2','Personal',1,''),(32,'2025-10-06 15:12:44',NULL,51,'3','Maternity',1,''),(33,'2025-10-06 15:12:44',NULL,51,'4','Compassionate',1,''),(34,'2025-10-06 15:12:44',NULL,51,'5','Annual',1,''),(35,'2025-10-06 15:12:44',NULL,51,'6','Business Trip',1,''),(36,'2025-10-06 15:12:44',NULL,53,'1000','LeaveClass1 object',1,''),(37,'2025-10-06 15:12:44',NULL,53,'1001','LeaveClass1 object',1,''),(38,'2025-10-06 15:12:44',NULL,53,'1002','LeaveClass1 object',1,''),(39,'2025-10-06 15:12:44',NULL,53,'1003','LeaveClass1 object',1,''),(40,'2025-10-06 15:12:44',NULL,53,'1004','LeaveClass1 object',1,''),(41,'2025-10-06 15:12:44',NULL,53,'1005','LeaveClass1 object',1,''),(42,'2025-10-06 15:12:44',NULL,53,'1008','LeaveClass1 object',1,''),(43,'2025-10-06 15:12:44',NULL,53,'1009','LeaveClass1 object',1,''),(44,'2025-10-06 15:12:44',NULL,47,'1','Flexible shift',1,''),(45,'2025-10-06 15:12:44',NULL,46,'1','Flexible TimeTable',1,''),(46,'2025-10-06 15:12:44',NULL,48,'1','Flexible shift,Flexible TimeTable',1,''),(47,'2025-10-06 15:12:44',NULL,48,'2','Flexible shift,Flexible TimeTable',1,''),(48,'2025-10-06 15:12:44',NULL,48,'3','Flexible shift,Flexible TimeTable',1,''),(49,'2025-10-06 15:12:44',NULL,48,'4','Flexible shift,Flexible TimeTable',1,''),(50,'2025-10-06 15:12:44',NULL,48,'5','Flexible shift,Flexible TimeTable',1,''),(51,'2025-10-06 15:12:44',NULL,48,'6','Flexible shift,Flexible TimeTable',1,''),(52,'2025-10-06 15:12:44',NULL,48,'7','Flexible shift,Flexible TimeTable',1,''),(53,'2025-10-06 15:12:44',NULL,13,'15','Attendance.default access control page',1,''),(54,'2025-10-06 15:12:44',NULL,65,'1','24-Hour Accessible',1,''),(55,'2025-10-06 15:12:44',NULL,67,'1','Auto',1,''),(56,'2025-10-06 15:12:44',NULL,67,'2','Wiegand 26',1,''),(57,'2025-10-06 15:12:44',NULL,67,'3','Wiegand 26a',1,''),(58,'2025-10-06 15:12:44',NULL,67,'4','Wiegand 34',1,''),(59,'2025-10-06 15:12:44',NULL,67,'5','Wiegand 34a',1,''),(60,'2025-10-06 15:12:44',NULL,67,'6','Wiegand 36',1,''),(61,'2025-10-06 15:12:44',NULL,67,'7','Wiegand 37',1,''),(62,'2025-10-06 15:12:44',NULL,67,'8','Wiegand 37a',1,''),(63,'2025-10-06 15:12:44',NULL,67,'9','Wiegand 50',1,''),(64,'2025-10-06 15:12:44',NULL,67,'10','Wiegand 66',1,''),(65,'2025-10-06 15:12:44',NULL,67,'11','Wiegand 35',1,''),(66,'2025-10-06 15:12:45',NULL,13,'16','Access Control System.default access control page',1,''),(67,'2025-10-06 15:12:45',NULL,13,'17','elevator.Default Page of Elevator Control System',1,''),(68,'2025-10-06 15:12:45',NULL,13,'18','video.Default page of Video',1,''),(69,'2025-10-06 15:12:45',NULL,13,'19','visitor.Visitors default Page',1,''),(70,'2025-10-06 15:14:13',1,NULL,'1','',5,''),(71,'2025-10-06 15:14:14',1,9,'1','[en] content type.app_label: worktable -> worktable',1,''),(72,'2025-10-06 15:14:14',1,9,'2','[en] content type.app_label: dbapp -> dbapp',1,''),(73,'2025-10-06 15:14:14',1,9,'3','[en] content type.app_label: auth -> auth',1,''),(74,'2025-10-06 15:14:14',1,9,'4','[en] content type.app_label: django_extensions -> django_extensions',1,''),(75,'2025-10-06 15:14:55',1,4,'1','admin',2,''),(76,'2025-10-06 15:15:05',1,NULL,'1','',5,''),(77,'2025-10-06 15:15:08',1,9,'5','[en] Basic code table.display: Simplified Chinese -> Simplified Chinese',1,''),(78,'2025-10-06 15:15:08',1,9,'6','[en] Basic code table.display: English -> English',1,''),(79,'2025-10-06 15:15:08',1,9,'7','[en] Basic code table.display: Spanish -> Spanish',1,''),(80,'2025-10-06 15:15:08',1,9,'8','[en] Basic code table.display: Traditional Chinese -> Traditional Chinese',1,''),(81,'2025-10-06 15:15:08',1,9,'9','[en] Basic code table.display: Polish -> Polish',1,''),(82,'2025-10-06 15:15:08',1,9,'10','[en] Basic code table.display: French -> French',1,''),(83,'2025-10-06 15:15:08',1,9,'11','[en] Basic code table.display: Arabic -> Arabic',1,''),(84,'2025-10-06 15:15:08',1,9,'12','[en] Basic code table.display: Vietnamese -> Vietnamese',1,''),(85,'2025-10-06 15:15:08',1,9,'13','[en] Basic code table.display: Thai -> Thai',1,''),(86,'2025-10-06 15:15:08',1,9,'14','[en] Basic code table.display: Russian -> Russian',1,''),(87,'2025-10-06 15:15:08',1,9,'15','[en] Basic code table.display: Portuguese -> Portuguese',1,''),(88,'2025-10-06 15:15:08',1,9,'16','[en] Basic code table.display: Italian -> Italian',1,''),(89,'2025-10-10 08:01:32',1,NULL,'1','',5,''),(90,'2025-10-14 12:47:54',1,NULL,'1','',5,''),(91,'2025-10-16 14:57:32',1,NULL,'1','',5,''),(92,'2025-10-17 08:38:39',1,NULL,'1','',5,''),(93,'2025-10-20 09:29:39',1,NULL,'1','',5,'');
/*!40000 ALTER TABLE `action_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `areaadmin`
--

DROP TABLE IF EXISTS `areaadmin`;
CREATE TABLE `areaadmin` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `areaadmin_user_id` (`user_id`),
  KEY `areaadmin_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `areaadmin`
--

LOCK TABLES `areaadmin` WRITE;
/*!40000 ALTER TABLE `areaadmin` DISABLE KEYS */;
/*!40000 ALTER TABLE `areaadmin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `att_attreport`
--

DROP TABLE IF EXISTS `att_attreport`;
CREATE TABLE `att_attreport` (
  `ItemName` varchar(100) NOT NULL,
  `ItemType` varchar(20) default NULL,
  `Author_id` int(11) NOT NULL,
  `ItemValue` longtext,
  `Published` smallint(6) default NULL,
  PRIMARY KEY  (`ItemName`),
  KEY `att_attreport_Author_id` (`Author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `att_attreport`
--

LOCK TABLES `att_attreport` WRITE;
/*!40000 ALTER TABLE `att_attreport` DISABLE KEYS */;
/*!40000 ALTER TABLE `att_attreport` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `att_overtime`
--

DROP TABLE IF EXISTS `att_overtime`;
CREATE TABLE `att_overtime` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `emp_id` int(11) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `remark` varchar(200) default NULL,
  `audit_status` int(11) NOT NULL,
  `auditreason` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `emp_id` (`emp_id`,`starttime`,`endtime`),
  KEY `att_overtime_emp_id` (`emp_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `att_overtime`
--

LOCK TABLES `att_overtime` WRITE;
/*!40000 ALTER TABLE `att_overtime` DISABLE KEYS */;
/*!40000 ALTER TABLE `att_overtime` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `att_waitforprocessdata`
--

DROP TABLE IF EXISTS `att_waitforprocessdata`;
CREATE TABLE `att_waitforprocessdata` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `flag` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `att_waitforprocessdata_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `att_waitforprocessdata`
--

LOCK TABLES `att_waitforprocessdata` WRITE;
/*!40000 ALTER TABLE `att_waitforprocessdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `att_waitforprocessdata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attcalclog`
--

DROP TABLE IF EXISTS `attcalclog`;
CREATE TABLE `attcalclog` (
  `id` int(11) NOT NULL auto_increment,
  `DeptID` int(11) default NULL,
  `UserId` int(11) NOT NULL,
  `StartDate` datetime default NULL,
  `EndDate` datetime NOT NULL,
  `OperTime` datetime NOT NULL,
  `Type` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attcalclog`
--

LOCK TABLES `attcalclog` WRITE;
/*!40000 ALTER TABLE `attcalclog` DISABLE KEYS */;
/*!40000 ALTER TABLE `attcalclog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attexception`
--

DROP TABLE IF EXISTS `attexception`;
CREATE TABLE `attexception` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserId` int(11) NOT NULL,
  `StartTime` datetime NOT NULL,
  `EndTime` datetime NOT NULL,
  `ExceptionID` int(11) default NULL,
  `AuditExcID` int(11) default NULL,
  `OldAuditExcID` int(11) default NULL,
  `OverlapTime` int(11) default NULL,
  `TimeLong` int(11) default NULL,
  `InScopeTime` int(11) default NULL,
  `AttDate` datetime default NULL,
  `OverlapWorkDayTail` int(11) NOT NULL,
  `OverlapWorkDay` double default NULL,
  `schindex` int(11) default NULL,
  `Minsworkday` int(11) default NULL,
  `Minsworkday1` int(11) default NULL,
  `schid` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserId` (`UserId`,`AttDate`,`StartTime`),
  KEY `attexception_UserId` (`UserId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attexception`
--

LOCK TABLES `attexception` WRITE;
/*!40000 ALTER TABLE `attexception` DISABLE KEYS */;
/*!40000 ALTER TABLE `attexception` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attparam`
--

DROP TABLE IF EXISTS `attparam`;
CREATE TABLE `attparam` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `ParaName` varchar(20) NOT NULL,
  `ParaType` varchar(2) default NULL,
  `ParaValue` varchar(100) NOT NULL,
  PRIMARY KEY  (`ParaName`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attparam`
--

LOCK TABLES `attparam` WRITE;
/*!40000 ALTER TABLE `attparam` DISABLE KEYS */;
INSERT INTO `attparam` VALUES (NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'CompanyLogo',NULL,'Department Name');
/*!40000 ALTER TABLE `attparam` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attrecabnormite`
--

DROP TABLE IF EXISTS `attrecabnormite`;
CREATE TABLE `attrecabnormite` (
  `id` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `checktime` datetime NOT NULL,
  `CheckType` varchar(5) NOT NULL,
  `NewType` varchar(2) default NULL,
  `AbNormiteID` int(11) default NULL,
  `SchID` int(11) default NULL,
  `OP` int(11) default NULL,
  `AttDate` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `userid` (`userid`,`AttDate`,`checktime`),
  KEY `attrecabnormite_userid` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attrecabnormite`
--

LOCK TABLES `attrecabnormite` WRITE;
/*!40000 ALTER TABLE `attrecabnormite` DISABLE KEYS */;
/*!40000 ALTER TABLE `attrecabnormite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attshifts`
--

DROP TABLE IF EXISTS `attshifts`;
CREATE TABLE `attshifts` (
  `id` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `SchIndex` int(11) default NULL,
  `AutoSch` smallint(6) default NULL,
  `AttDate` datetime NOT NULL,
  `SchId` int(11) default NULL,
  `ClockInTime` datetime NOT NULL,
  `ClockOutTime` datetime NOT NULL,
  `StartTime` datetime default NULL,
  `EndTime` datetime default NULL,
  `WorkDay` double default NULL,
  `RealWorkDay` double default NULL,
  `NoIn` smallint(6) default NULL,
  `NoOut` smallint(6) default NULL,
  `Late` double default NULL,
  `Early` double default NULL,
  `Absent` double default NULL,
  `OverTime` double default NULL,
  `WorkTime` int(11) default NULL,
  `ExceptionID` int(11) default NULL,
  `Symbol` varchar(50) default NULL,
  `MustIn` smallint(6) default NULL,
  `MustOut` smallint(6) default NULL,
  `OverTime1` int(11) default NULL,
  `WorkMins` int(11) default NULL,
  `SSpeDayNormal` double default NULL,
  `SSpeDayWeekend` double default NULL,
  `SSpeDayHoliday` double default NULL,
  `AttTime` int(11) default NULL,
  `SSpeDayNormalOT` double default NULL,
  `SSpeDayWeekendOT` double default NULL,
  `SSpeDayHolidayOT` double default NULL,
  `AbsentMins` int(11) default NULL,
  `AttChkTime` varchar(10) default NULL,
  `AbsentR` double default NULL,
  `ScheduleName` varchar(20) default NULL,
  `IsConfirm` smallint(6) default NULL,
  `IsRead` smallint(6) default NULL,
  `Exception` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `userid` (`userid`,`AttDate`,`SchId`,`StartTime`),
  KEY `attshifts_userid` (`userid`),
  KEY `attshifts_SchId` (`SchId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attshifts`
--

LOCK TABLES `attshifts` WRITE;
/*!40000 ALTER TABLE `attshifts` DISABLE KEYS */;
/*!40000 ALTER TABLE `attshifts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'role_for_employee');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL auto_increment,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id` (`group_id`),
  KEY `auth_group_permissions_permission_id` (`permission_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2755 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
INSERT INTO `auth_group_permissions` VALUES (2754,1,321),(2753,1,357),(2752,1,356),(2751,1,353),(2750,1,352),(2749,1,194),(2748,1,198),(2747,1,197),(2746,1,196),(2745,1,195),(2744,1,578),(2743,1,577),(2742,1,576),(2741,1,575),(2740,1,318),(2739,1,317),(2738,1,315),(2737,1,314),(2736,1,311),(2735,1,310),(2734,1,307),(2733,1,306),(2732,1,305),(2731,1,304),(2730,1,303),(2729,1,302),(2728,1,300),(2727,1,299),(2726,1,193),(2725,1,287),(2724,1,322),(2723,1,266),(2722,1,392),(2721,1,391);
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `auth_message_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=589 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'浏览会话',1,'browse_session'),(2,'Can add session',1,'add_session'),(3,'Can change session',1,'change_session'),(4,'Can delete session',1,'delete_session'),(5,'浏览content type',6,'browse_contenttype'),(6,'浏览角色',3,'browse_group'),(7,'删除',3,'groupdel_group'),(8,'浏览message',5,'browse_message'),(9,'浏览权限',2,'browse_permission'),(10,'浏览用户',4,'browse_user'),(11,'删除',4,'delete_user'),(12,'Can add permission',2,'add_permission'),(13,'Can change permission',2,'change_permission'),(14,'Can delete permission',2,'delete_permission'),(15,'Can add 角色',3,'add_group'),(16,'Can change 角色',3,'change_group'),(17,'Can delete 角色',3,'delete_group'),(18,'Can add 用户',4,'add_user'),(19,'Can change 用户',4,'change_user'),(20,'Can add message',5,'add_message'),(21,'Can change message',5,'change_message'),(22,'Can delete message',5,'delete_message'),(23,'Can add content type',6,'add_contenttype'),(24,'Can change content type',6,'change_contenttype'),(25,'Can delete content type',6,'delete_contenttype'),(26,'浏览系统参数',15,'browse_appoption'),(27,'新增',15,'add_appoption'),(28,'修改',15,'change_appoption'),(29,'清空记录',15,'clear_appoption'),(30,'删除',15,'delete_appoption'),(31,'导出',15,'dataexport_appoption'),(32,'浏览基础代码表',12,'browse_basecode'),(33,'新增',12,'add_basecode'),(34,'修改',12,'change_basecode'),(35,'删除',12,'delete_basecode'),(36,'导出',12,'dataexport_basecode'),(37,'浏览翻译为数据',9,'browse_datatranslation'),(38,'新增',9,'add_datatranslation'),(39,'修改',9,'change_datatranslation'),(40,'删除',9,'delete_datatranslation'),(41,'导出',9,'dataexport_datatranslation'),(42,'浏览日志记录',7,'browse_logentry'),(43,'导出',7,'dataexport_logentry'),(44,'浏览个性设置',13,'browse_option'),(45,'新增',13,'add_option'),(46,'修改',13,'change_option'),(47,'删除',13,'delete_option'),(48,'导出',13,'dataexport_option'),(49,'浏览个人选项',16,'browse_personaloption'),(50,'新增',16,'add_personaloption'),(51,'修改',16,'change_personaloption'),(52,'删除',16,'delete_personaloption'),(53,'导出',16,'dataexport_personaloption'),(54,'浏览str resource',11,'browse_strresource'),(55,'新增',11,'add_strresource'),(56,'修改',11,'change_strresource'),(57,'删除',11,'delete_strresource'),(58,'导出',11,'dataexport_strresource'),(59,'浏览翻译为字符串资源',10,'browse_strtranslation'),(60,'新增',10,'add_strtranslation'),(61,'修改',10,'change_strtranslation'),(62,'删除',10,'delete_strtranslation'),(63,'导出',10,'dataexport_strtranslation'),(64,'浏览系统参数',14,'browse_systemoption'),(65,'新增',14,'add_systemoption'),(66,'修改',14,'change_systemoption'),(67,'删除',14,'delete_systemoption'),(68,'导出',14,'dataexport_systemoption'),(69,'Can add 日志记录',7,'add_logentry'),(70,'Can change 日志记录',7,'change_logentry'),(71,'Can delete 日志记录',7,'delete_logentry'),(72,'Can add 增加的数据',8,'add_additiondata'),(73,'Can change 增加的数据',8,'change_additiondata'),(74,'Can delete 增加的数据',8,'delete_additiondata'),(75,'Can add 用户指纹',17,'add_operatortemplate'),(76,'Can change 用户指纹',17,'change_operatortemplate'),(77,'Can delete 用户指纹',17,'delete_operatortemplate'),(78,'浏览数据库管理',18,'browse_dbbackuplog'),(79,'备份数据库',18,'opbackupdb_dbbackuplog'),(80,'初始化数据库',18,'opinitdb_dbbackuplog'),(81,'还原数据库',18,'oprestoredb_dbbackuplog'),(82,'新增',18,'add_dbbackuplog'),(83,'修改',18,'change_dbbackuplog'),(84,'删除',18,'delete_dbbackuplog'),(85,'导出',18,'dataexport_dbbackuplog'),(86,'还原数据库',6,'can_Restore_db'),(87,'浏览view model',19,'browse_viewmodel'),(88,'新增',19,'add_viewmodel'),(89,'修改',19,'change_viewmodel'),(90,'删除',19,'delete_viewmodel'),(91,'导出',19,'dataexport_viewmodel'),(92,'系统参数设置',6,'can_sys_option'),(93,'个性设置',6,'can_user_option'),(94,'浏览多卡开门人员组',21,'browse_accmorecardempgroup'),(95,'添加人员',21,'opaddemptomcegroup_accmorecardempgroup'),(96,'删除人员',21,'opdelempfrommcegroup_accmorecardempgroup'),(97,'新增',21,'add_accmorecardempgroup'),(98,'修改',21,'change_accmorecardempgroup'),(99,'删除',21,'delete_accmorecardempgroup'),(100,'导出',21,'dataexport_accmorecardempgroup'),(101,'浏览区域设置',22,'browse_area'),(102,'为区域添加人员',22,'opadjustarea_area'),(103,'同步所有区域信息到分控',22,'opsyncallareatobranch_area'),(104,'同步区域信息到分控',22,'opsynconeareatobranch_area'),(105,'新增',22,'add_area'),(106,'修改',22,'change_area'),(107,'撤消区域',22,'delete_area'),(108,'导出',22,'dataexport_area'),(109,'浏览卡类型',26,'browse_cardtype'),(110,'新增',26,'add_cardtype'),(111,'修改',26,'change_cardtype'),(112,'删除',26,'delete_cardtype'),(113,'导出',26,'dataexport_cardtype'),(114,'浏览部门',20,'browse_department'),(115,'同步所有部门信息到分控',20,'opsyncalldepttobranch_department'),(116,'同步部门信息到分控',20,'opsynconedepttobranch_department'),(117,'新增',20,'add_department'),(118,'修改',20,'change_department'),(119,'撤消',20,'delete_department'),(120,'导出',20,'dataexport_department'),(121,'导入',20,'dataimport_department'),(122,'浏览人员调动',28,'browse_empchange'),(123,'立即生效',28,'opavailable_empchange'),(124,'新增',28,'add_empchange'),(125,'修改',28,'change_empchange'),(126,'',28,'delete_empchange'),(127,'导出',28,'dataexport_empchange'),(128,'浏览人事报表',24,'browse_empitemdefine'),(129,'部门花名册',24,'deptrosterreport_empitemdefine'),(130,'人员卡片清单',24,'empcardreport_empitemdefine'),(131,'学历构成分析表',24,'empeducationreport_empitemdefine'),(132,'人员流动表',24,'empflowreport_empitemdefine'),(133,'导出',24,'dataexport_empitemdefine'),(134,'浏览人员',23,'browse_employee'),(135,'添加所属权限组',23,'opaddleveltoemp_employee'),(136,'调整区域',23,'opadjustarea_employee'),(137,'调整部门',23,'opadjustdept_employee'),(138,'制卡',23,'opcardprinting_employee'),(139,'删除所属权限组',23,'opdellevelfromemp_employee'),(140,'员工转正',23,'opemptype_employee'),(141,'人员发卡',23,'opissuecard_employee'),(142,'离职',23,'opleave_employee'),(143,'挂失卡',23,'oplosecard_employee'),(144,'登记指纹',23,'opregisterfinger_employee'),(145,'解挂卡',23,'oprevertcard_employee'),(146,'同步人员到设备',23,'opsynctodevice_employee'),(147,'职务调动',23,'optitilechange_employee'),(148,'上传个人照片',23,'opuploadphoto_employee'),(149,'新增',23,'add_employee'),(150,'修改',23,'change_employee'),(151,'删除',23,'delete_employee'),(152,'导出',23,'dataexport_employee'),(153,'导入',23,'dataimport_employee'),(154,'浏览人员发卡',27,'browse_issuecard'),(155,'批量发卡',27,'opbatchissuecard_issuecard'),(156,'新增',27,'add_issuecard'),(157,'修改',27,'change_issuecard'),(158,'删除',27,'delete_issuecard'),(159,'导出',27,'dataexport_issuecard'),(160,'浏览人员离职',25,'browse_leavelog'),(161,'关闭门禁',25,'opcloseaccess_leavelog'),(162,'关闭考勤',25,'opcloseatt_leavelog'),(163,'离职恢复',25,'oprestoreempleave_leavelog'),(164,'新增',25,'add_leavelog'),(165,'',25,'change_leavelog'),(166,'删除',25,'delete_leavelog'),(167,'导出',25,'dataexport_leavelog'),(168,'导航',6,'can_PersonnelGuide'),(169,'Can add 人事报表',24,'add_empitemdefine'),(170,'Can change 人事报表',24,'change_empitemdefine'),(171,'Can delete 人事报表',24,'delete_empitemdefine'),(172,'数据清理',6,'can_DeleteData'),(173,'浏览系统提醒设置',30,'browse_groupmsg'),(174,'新增',30,'add_groupmsg'),(175,'修改',30,'change_groupmsg'),(176,'删除',30,'delete_groupmsg'),(177,'导出',30,'dataexport_groupmsg'),(178,'浏览公告发布',32,'browse_instantmsg'),(179,'新增',32,'add_instantmsg'),(180,'修改',32,'change_instantmsg'),(181,'删除',32,'delete_instantmsg'),(182,'导出',32,'dataexport_instantmsg'),(183,'浏览公告类别',29,'browse_msgtype'),(184,'新增',29,'add_msgtype'),(185,'修改',29,'change_msgtype'),(186,'删除',29,'delete_msgtype'),(187,'导出',29,'dataexport_msgtype'),(188,'浏览用户消息确认',31,'browse_usrmsg'),(189,'新增',31,'add_usrmsg'),(190,'修改',31,'change_usrmsg'),(191,'删除',31,'delete_usrmsg'),(192,'导出',31,'dataexport_usrmsg'),(193,'补签卡',6,'can_SelfCheckexact'),(194,'加班单',6,'can_SelfOverTime'),(195,'考勤报表',6,'can_SelfReport'),(196,'请假',6,'can_SelfSpecDay'),(197,'原始记录表',6,'can_SelfTransaction'),(198,'预约管理',6,'can_SelfVisitorReservation'),(199,'浏览区域管理',43,'browse_areaadmin'),(200,'浏览夏令时',33,'browse_dstime'),(201,'设置夏令时',33,'opsetdstime_dstime'),(202,'新增',33,'add_dstime'),(203,'修改',33,'change_dstime'),(204,'删除',33,'delete_dstime'),(205,'导出',33,'dataexport_dstime'),(206,'浏览部门管理',42,'browse_deptadmin'),(207,'浏览服务器下发命令',36,'browse_devcmd'),(208,'清空命令表',36,'opcleardevcmd_devcmd'),(209,'新增',36,'add_devcmd'),(210,'修改',36,'change_devcmd'),(211,'删除',36,'delete_devcmd'),(212,'导出',36,'dataexport_devcmd'),(213,'浏览失败命令查询',41,'browse_devcmdbak'),(214,'清空失败命令',41,'opcleardevcmd_devcmdbak'),(215,'新增',41,'add_devcmdbak'),(216,'修改',41,'change_devcmdbak'),(217,'删除',41,'delete_devcmdbak'),(218,'导出',41,'dataexport_devcmdbak'),(219,'浏览设备通讯日志',40,'browse_devlog'),(220,'导出',40,'dataexport_devlog'),(221,'设备监控',6,'can_DevRTMonitorPage'),(222,'浏览设备',34,'browse_device'),(223,'清除全部数据',34,'cleardata_device'),(224,'清除考勤图片',34,'clearpicture_device'),(225,'清除考勤记录',34,'cleartransaction_device'),(226,'设备功能',34,'devfunon_device'),(227,'修改IP地址',34,'opchangeipofacpanel_device'),(228,'修改指纹比对阈值',34,'opchangemthreshold_device'),(229,'控制辅助输出',34,'opctrlauxout_device'),(230,'禁用',34,'opdisabledevice_device'),(231,'启用',34,'openabledevice_device'),(232,'重新上传数据',34,'opreloaddata_device'),(233,'禁用夏令时',34,'opremovedstime_device'),(234,'搜索门禁控制器',34,'opsearchacpanel_device'),(235,'启用夏令时',34,'opsetdstime_device'),(236,'升级固件',34,'opupgradefirmware_device'),(237,'重启设备',34,'reboot_device'),(238,'获取设备信息',34,'refreshdeviceinfo_device'),(239,'修改通讯密码',34,'resetpassword_device'),(240,'同步时间',34,'syncacpaneltime_device'),(241,'同步所有数据',34,'syncdata_device'),(242,'获取事件记录',34,'uploadlogs_device'),(243,'获取人员信息',34,'uploaduserinfo_device'),(244,'新增',34,'add_device'),(245,'修改',34,'change_device'),(246,'删除',34,'delete_device'),(247,'导出',34,'dataexport_device'),(248,'导航',6,'can_IclockGuide'),(249,'浏览操作设备日志',39,'browse_oplog'),(250,'Transaction Monitor',39,'monitor_oplog'),(251,'浏览通信命令详情',35,'browse_operatecmd'),(252,'新增',35,'add_operatecmd'),(253,'编辑',35,'change_operatecmd'),(254,'删除',35,'delete_operatecmd'),(255,'导出',35,'dataexport_operatecmd'),(256,'浏览人员指纹',37,'browse_template'),(257,'新增',37,'add_template'),(258,'修改',37,'change_template'),(259,'删除',37,'delete_template'),(260,'导出',37,'dataexport_template'),(261,'浏览test data',44,'browse_testdata'),(262,'新增',44,'add_testdata'),(263,'修改',44,'change_testdata'),(264,'删除',44,'delete_testdata'),(265,'导出',44,'dataexport_testdata'),(266,'浏览原始记录表',38,'browse_transaction'),(267,'Clear Obsolete Data',38,'clearObsoleteData_transaction'),(268,'导出',38,'dataexport_transaction'),(269,'Can add 原始记录表',38,'add_transaction'),(270,'Can change 原始记录表',38,'change_transaction'),(271,'Can delete 原始记录表',38,'delete_transaction'),(272,'Can add 操作设备日志',39,'add_oplog'),(273,'Can change 操作设备日志',39,'change_oplog'),(274,'Can delete 操作设备日志',39,'delete_oplog'),(275,'Can add 设备通讯日志',40,'add_devlog'),(276,'Can change 设备通讯日志',40,'change_devlog'),(277,'Can delete 设备通讯日志',40,'delete_devlog'),(278,'Can add 部门管理',42,'add_deptadmin'),(279,'Can change 部门管理',42,'change_deptadmin'),(280,'Can delete 部门管理',42,'delete_deptadmin'),(281,'Can add 区域管理',43,'add_areaadmin'),(282,'Can change 区域管理',43,'change_areaadmin'),(283,'Can delete 区域管理',43,'delete_areaadmin'),(284,'考勤计算与报表',6,'can_AttCalculate'),(285,'考勤设备管理',6,'can_AttDeviceDataManage'),(286,'区域用户管理',6,'can_AttDeviceUserManage'),(287,'浏览att exception',57,'browse_attexception'),(288,'新增',57,'add_attexception'),(289,'修改',57,'change_attexception'),(290,'删除',57,'delete_attexception'),(291,'导出',57,'dataexport_attexception'),(292,'导航',6,'can_AttGuide'),(293,'浏览考勤参数',54,'browse_attparam'),(294,'新增',54,'add_attparam'),(295,'修改',54,'change_attparam'),(296,'删除',54,'delete_attparam'),(297,'导出',54,'dataexport_attparam'),(298,'浏览考勤报表',60,'browse_attreport'),(299,'统计结果详情',60,'calcresultdetail_attreport'),(300,'考勤汇总表',60,'calctotalreport_attreport'),(301,'统计',60,'calculate_attreport'),(302,'补签记录表',60,'checkexact_attreport'),(303,'每日考勤统计表',60,'earchdayattreport_attreport'),(304,'考勤异常表',60,'exceptionreport_attreport'),(305,'假类汇总',60,'leavetotalreport_attreport'),(306,'原始记录表',60,'orgbrushrecord_attreport'),(307,'其它考勤异常表',60,'otherexceptionreport_attreport'),(308,'导出',60,'dataexport_attreport'),(309,'员工排班',6,'can_AttUserOfRun'),(310,'浏览补签卡',61,'browse_checkexact'),(311,'新增补签卡',61,'opaddmanycheckexact_checkexact'),(312,'审批',61,'opauditcheckexact_checkexact'),(313,'新增',61,'add_checkexact'),(314,'修改',61,'change_checkexact'),(315,'删除',61,'delete_checkexact'),(316,'导出',61,'dataexport_checkexact'),(317,'浏览请假',52,'browse_empspecday'),(318,'新增请假',52,'opaddmanyuserid_empspecday'),(319,'审批',52,'opspecaudit_empspecday'),(320,'新增',52,'add_empspecday'),(321,'修改',52,'change_empspecday'),(322,'删除',52,'delete_empspecday'),(323,'导出',52,'dataexport_empspecday'),(324,'浏览考勤节假日',45,'browse_holiday'),(325,'新增',45,'add_holiday'),(326,'修改',45,'change_holiday'),(327,'删除',45,'delete_holiday'),(328,'导出',45,'dataexport_holiday'),(329,'浏览假类',51,'browse_leaveclass'),(330,'新增',51,'add_leaveclass'),(331,'修改',51,'change_leaveclass'),(332,'清空记录',51,'clear_leaveclass'),(333,'删除',51,'delete_leaveclass'),(334,'导出',51,'dataexport_leaveclass'),(335,'浏览统计项目表',53,'browse_leaveclass1'),(336,'新增',53,'add_leaveclass1'),(337,'修改',53,'change_leaveclass1'),(338,'删除',53,'delete_leaveclass1'),(339,'导出',53,'dataexport_leaveclass1'),(340,'浏览班次',47,'browse_num_run'),(341,'增加时间段',47,'opaddtimetable_num_run'),(342,'清空时间段',47,'opdeletetimetable_num_run'),(343,'新增',47,'add_num_run'),(344,'修改',47,'change_num_run'),(345,'删除',47,'delete_num_run'),(346,'导出',47,'dataexport_num_run'),(347,'浏览班次明细',48,'browse_num_run_deil'),(348,'新增',48,'add_num_run_deil'),(349,'修改',48,'change_num_run_deil'),(350,'删除',48,'delete_num_run_deil'),(351,'导出',48,'dataexport_num_run_deil'),(352,'浏览加班单',64,'browse_overtime'),(353,'新增加班单',64,'opaddmanyovertime_overtime'),(354,'审批',64,'opauditmanyemployee_overtime'),(355,'新增',64,'add_overtime'),(356,'修改',64,'change_overtime'),(357,'删除',64,'delete_overtime'),(358,'导出',64,'dataexport_overtime'),(359,'浏览考勤时段',46,'browse_schclass'),(360,'新增',46,'add_schclass'),(361,'修改',46,'change_schclass'),(362,'删除',46,'delete_schclass'),(363,'导出',46,'dataexport_schclass'),(364,'浏览调休',62,'browse_setuseratt'),(365,'新增',62,'opaddmanyobj_setuseratt'),(366,'新增',62,'add_setuseratt'),(367,'修改',62,'change_setuseratt'),(368,'删除',62,'delete_setuseratt'),(369,'导出',62,'dataexport_setuseratt'),(370,'浏览员工排班',50,'browse_user_of_run'),(371,'新增临时排班',50,'opaddtempshifts_user_of_run'),(372,'新增排班',50,'opadduserofrun_user_of_run'),(373,'清除排班记录',50,'opclearshift_user_of_run'),(374,'新增',50,'add_user_of_run'),(375,'修改',50,'change_user_of_run'),(376,'删除',50,'delete_user_of_run'),(377,'导出',50,'dataexport_user_of_run'),(378,'浏览临时排班',49,'browse_user_temp_sch'),(379,'清除临时排班记录',49,'opclearshift_user_temp_sch'),(380,'新增',49,'add_user_temp_sch'),(381,'修改',49,'change_user_temp_sch'),(382,'删除',49,'delete_user_temp_sch'),(383,'浏览',49,'dataexport_user_temp_sch'),(384,'浏览user used s classes',55,'browse_userusedsclasses'),(385,'浏览wait for process data',63,'browse_waitforprocessdata'),(386,'新增',63,'add_waitforprocessdata'),(387,'修改',63,'change_waitforprocessdata'),(388,'删除',63,'delete_waitforprocessdata'),(389,'导出',63,'dataexport_waitforprocessdata'),(390,'浏览att calc log',56,'browse_attcalclog'),(391,'浏览统计结果详情',58,'browse_attrecabnormite'),(392,'浏览考勤明细表',59,'browse_attshifts'),(393,'Can add user used s classes',55,'add_userusedsclasses'),(394,'Can change user used s classes',55,'change_userusedsclasses'),(395,'Can delete user used s classes',55,'delete_userusedsclasses'),(396,'Can add att calc log',56,'add_attcalclog'),(397,'Can change att calc log',56,'change_attcalclog'),(398,'Can delete att calc log',56,'delete_attcalclog'),(399,'Can add 统计结果详情',58,'add_attrecabnormite'),(400,'Can change 统计结果详情',58,'change_attrecabnormite'),(401,'Can delete 统计结果详情',58,'delete_attrecabnormite'),(402,'Can add 考勤明细表',59,'add_attshifts'),(403,'Can change 考勤明细表',59,'change_attshifts'),(404,'Can delete 考勤明细表',59,'delete_attshifts'),(405,'Can add 考勤报表',60,'add_attreport'),(406,'Can change 考勤报表',60,'change_attreport'),(407,'Can delete 考勤报表',60,'delete_attreport'),(408,'浏览反潜设置',76,'browse_accantiback'),(409,'新增',76,'add_accantiback'),(410,'修改',76,'change_accantiback'),(411,'删除',76,'delete_accantiback'),(412,'导出',76,'dataexport_accantiback'),(413,'浏览门禁设备扩展参数',70,'browse_accdevice'),(414,'新增',70,'add_accdevice'),(415,'修改',70,'change_accdevice'),(416,'删除',70,'delete_accdevice'),(417,'导出',70,'dataexport_accdevice'),(418,'浏览门',68,'browse_accdoor'),(419,'新增',68,'add_accdoor'),(420,'修改',68,'change_accdoor'),(421,'删除',68,'delete_accdoor'),(422,'导出',68,'dataexport_accdoor'),(423,'浏览首卡常开设置',73,'browse_accfirstopen'),(424,'添加开门人员',73,'opaddemptofcopen_accfirstopen'),(425,'删除开门人员',73,'opdelempfromfcopen_accfirstopen'),(426,'新增',73,'add_accfirstopen'),(427,'修改',73,'change_accfirstopen'),(428,'删除',73,'delete_accfirstopen'),(429,'导出',73,'dataexport_accfirstopen'),(430,'浏览全局反潜设置',81,'browse_accglobalapb'),(431,'新增',81,'add_accglobalapb'),(432,'修改',81,'change_accglobalapb'),(433,'删除',81,'delete_accglobalapb'),(434,'导出',81,'dataexport_accglobalapb'),(435,'浏览全局反潜组设置',80,'browse_accglobalapbgroup'),(436,'新增',80,'add_accglobalapbgroup'),(437,'修改',80,'change_accglobalapbgroup'),(438,'删除',80,'delete_accglobalapbgroup'),(439,'导出',80,'dataexport_accglobalapbgroup'),(440,'浏览门禁节假日',78,'browse_accholidays'),(441,'新增',78,'add_accholidays'),(442,'修改',78,'change_accholidays'),(443,'删除',78,'delete_accholidays'),(444,'导出',78,'dataexport_accholidays'),(445,'浏览互锁设置',77,'browse_accinterlock'),(446,'新增',77,'add_accinterlock'),(447,'修改',77,'change_accinterlock'),(448,'删除',77,'delete_accinterlock'),(449,'导出',77,'dataexport_accinterlock'),(450,'浏览门禁权限组',79,'browse_acclevelset'),(451,'添加人员',79,'opaddemptolevel_acclevelset'),(452,'删除人员',79,'opdelempfromlevel_acclevelset'),(453,'新增',79,'add_acclevelset'),(454,'修改',79,'change_acclevelset'),(455,'删除',79,'delete_acclevelset'),(456,'导出',79,'dataexport_acclevelset'),(457,'浏览联动设置',72,'browse_acclinkageio'),(458,'新增',72,'add_acclinkageio'),(459,'修改',72,'change_acclinkageio'),(460,'删除',72,'delete_acclinkageio'),(461,'导出',72,'dataexport_acclinkageio'),(462,'浏览电子地图',66,'browse_accmap'),(463,'添加门',66,'opadddoorsontomap_accmap'),(464,'放大',66,'openlargemapdoor_accmap'),(465,'缩小',66,'opreducemapdoor_accmap'),(466,'移除门',66,'opremovedoorfrommap_accmap'),(467,'保存位置信息',66,'opsavemapdoorpos_accmap'),(468,'新增',66,'add_accmap'),(469,'修改',66,'change_accmap'),(470,'删除',66,'delete_accmap'),(471,'导出',66,'dataexport_accmap'),(472,'浏览门坐标',69,'browse_accmapdoorpos'),(473,'新增',69,'add_accmapdoorpos'),(474,'修改',69,'change_accmapdoorpos'),(475,'删除',69,'delete_accmapdoorpos'),(476,'导出',69,'dataexport_accmapdoorpos'),(477,'浏览多卡开门组',75,'browse_accmorecardgroup'),(478,'新增',75,'add_accmorecardgroup'),(479,'修改',75,'change_accmorecardgroup'),(480,'删除',75,'delete_accmorecardgroup'),(481,'导出',75,'dataexport_accmorecardgroup'),(482,'浏览多卡开门设置',74,'browse_accmorecardset'),(483,'新增',74,'add_accmorecardset'),(484,'修改',74,'change_accmorecardset'),(485,'删除',74,'delete_accmorecardset'),(486,'导出',74,'dataexport_accmorecardset'),(487,'门禁参数设置',6,'can_AccOption'),(488,'浏览实时监控记录',71,'browse_accrtmonitor'),(489,'清空异常事件记录',71,'opclearabnormitylogs_accrtmonitor'),(490,'清空全部事件记录',71,'opclearrtlogs_accrtmonitor'),(491,'新增',71,'add_accrtmonitor'),(492,'修改',71,'change_accrtmonitor'),(493,'删除',71,'delete_accrtmonitor'),(494,'导出',71,'dataexport_accrtmonitor'),(495,'浏览读头',82,'browse_accreader'),(496,'新增',82,'add_accreader'),(497,'修改',82,'change_accreader'),(498,'删除',82,'delete_accreader'),(499,'导出',82,'dataexport_accreader'),(500,'浏览门禁时间段',65,'browse_acctimeseg'),(501,'新增',65,'add_acctimeseg'),(502,'修改',65,'change_acctimeseg'),(503,'删除',65,'delete_acctimeseg'),(504,'导出',65,'dataexport_acctimeseg'),(505,'浏览韦根卡格式',67,'browse_accwiegandfmt'),(506,'重置默认设置',67,'initwgfmt_accwiegandfmt'),(507,'新增',67,'add_accwiegandfmt'),(508,'修改',67,'change_accwiegandfmt'),(509,'删除',67,'delete_accwiegandfmt'),(510,'导出',67,'dataexport_accwiegandfmt'),(511,'门禁异常事件',6,'can_AlarmEventReportPage'),(512,'全部门禁事件',6,'can_AllEventReportPage'),(513,'浏览辅助输入输出',83,'browse_auxiliary'),(514,'新增',83,'add_auxiliary'),(515,'修改',83,'change_auxiliary'),(516,'删除',83,'delete_auxiliary'),(517,'导出',83,'dataexport_auxiliary'),(518,'辅助点管理',6,'can_AuxiliaryPage'),(519,'门管理',6,'can_DoorMngPage'),(520,'门设置',6,'can_DoorSetPage'),(521,'电子地图',6,'can_ElectroMapPage'),(522,'浏览邮件',84,'browse_emailrecord'),(523,'清空全部邮件记录',84,'opclearrtlogs_emailrecord'),(524,'新增',84,'add_emailrecord'),(525,'修改',84,'change_emailrecord'),(526,'删除',84,'delete_emailrecord'),(527,'导出',84,'dataexport_emailrecord'),(528,'邮件',6,'can_EmailRecordFormPage'),(529,'以人员显示',6,'can_EmpLevelByEmpPage'),(530,'以权限组显示',6,'can_EmpLevelByLevelPage'),(531,'人员门禁权限',6,'can_EmpLevelReportPage'),(532,'人员门禁权限设置',6,'can_EmpLevelSetPage'),(533,'报警事件',6,'can_MonitorAlarmPage'),(534,'监控全部',6,'can_MonitorAllPage'),(535,'实时监控',6,'can_RTMonitorPage'),(536,'报表',6,'can_ReportFormPage'),(537,'人员电梯权限设置',6,'can_EleEmpLevelSetPage'),(538,'首卡常开',6,'can_EleFirstOpenPage'),(539,'以人员显示',6,'can_EmpLevelByEleEmpPage'),(540,'以权限组显示',6,'can_EmpLevelByEleLevelPage'),(541,'梯控权限组',6,'can_FloorLevelSetPage'),(542,'楼层设置',6,'can_FloorMngPage'),(543,'通道管理',6,'can_ChannelMngPage'),(544,'监控时是否弹出',6,'can_ShowVideoWhileMonitoring'),(545,'浏览视频通道',85,'browse_vidchannel'),(546,'新增',85,'add_vidchannel'),(547,'修改',85,'change_vidchannel'),(548,'删除',85,'delete_vidchannel'),(549,'导出',85,'dataexport_vidchannel'),(550,'视频参数设置',6,'can_VidOption'),(551,'视频事件记录',6,'can_VideoEventPage'),(552,'视频联动记录',6,'can_VideoLinkagePage'),(553,'浏览视频通道坐标',86,'browse_videomapchannelpos'),(554,'新增',86,'add_videomapchannelpos'),(555,'修改',86,'change_videomapchannelpos'),(556,'删除',86,'delete_videomapchannelpos'),(557,'导出',86,'dataexport_videomapchannelpos'),(558,'视频预览',6,'can_VideoPreviewPage'),(559,'访客基本资料',6,'can_BaseDataPage'),(560,'浏览登记地点',89,'browse_visplace'),(561,'新增',89,'add_visplace'),(562,'修改',89,'change_visplace'),(563,'删除',89,'delete_visplace'),(564,'导出',89,'dataexport_visplace'),(565,'浏览来访事由 ',87,'browse_visreason'),(566,'新增',87,'add_visreason'),(567,'修改',87,'change_visreason'),(568,'删除',87,'delete_visreason'),(569,'导出',87,'dataexport_visreason'),(570,'浏览访客历史记录',91,'browse_visreport'),(571,'新增',91,'add_visreport'),(572,'详情',91,'change_visreport'),(573,'删除',91,'delete_visreport'),(574,'导出',91,'dataexport_visreport'),(575,'浏览预约管理',88,'browse_visreservation'),(576,'新增',88,'add_visreservation'),(577,'修改',88,'change_visreservation'),(578,'删除',88,'delete_visreservation'),(579,'导出',88,'dataexport_visreservation'),(580,'浏览访客管理',90,'browse_visvisitor'),(581,'离开登记',90,'opleaveregister_visvisitor'),(582,'进入登记',90,'add_visvisitor'),(583,'编辑',90,'change_visvisitor'),(584,'删除',90,'delete_visvisitor'),(585,'导出',90,'dataexport_visvisitor'),(586,'访客单',6,'can_VisitorFormPage'),(587,'访客权限设置',6,'can_VisitorLevelSetPage'),(588,'参数设置',6,'can_VisitorOptionPage');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL auto_increment,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','','','','sha1$44a07$fca75fd498dd928870f72fe4e082e096a030f505',1,1,1,'2025-10-20 09:29:39','2025-10-06 15:12:42'),(2,'employee','','','employee@sinna.com','sha1$c3630$2713835efb9af4864679b58c1e2a1f424967fc7f',1,1,0,'2025-10-06 15:12:42','2025-10-06 15:12:42');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_user_id` (`user_id`),
  KEY `auth_user_groups_group_id` (`group_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
INSERT INTO `auth_user_groups` VALUES (1,2,1);
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_user_id` (`user_id`),
  KEY `auth_user_user_permissions_permission_id` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_additiondata`
--

DROP TABLE IF EXISTS `base_additiondata`;
CREATE TABLE `base_additiondata` (
  `id` int(11) NOT NULL auto_increment,
  `create_time` datetime NOT NULL,
  `user_id` int(11) default NULL,
  `content_type_id` int(11) default NULL,
  `object_id` varchar(100) NOT NULL,
  `key` varchar(64) NOT NULL,
  `value` varchar(128) NOT NULL,
  `data` longtext NOT NULL,
  `delete_time` datetime default NULL,
  PRIMARY KEY  (`id`),
  KEY `base_additiondata_user_id` (`user_id`),
  KEY `base_additiondata_content_type_id` (`content_type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_additiondata`
--

LOCK TABLES `base_additiondata` WRITE;
/*!40000 ALTER TABLE `base_additiondata` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_additiondata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_appoption`
--

DROP TABLE IF EXISTS `base_appoption`;
CREATE TABLE `base_appoption` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `optname` varchar(50) NOT NULL,
  `value` varchar(100) NOT NULL,
  `discribe` varchar(100) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_appoption`
--

LOCK TABLES `base_appoption` WRITE;
/*!40000 ALTER TABLE `base_appoption` DISABLE KEYS */;
INSERT INTO `base_appoption` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'company','Company Name','Company Name'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'dbversion','5.31','version'),(3,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'date_format','%m/%d/%Y','Date Format'),(4,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'browse_title','Access Control System','Browser Title');
/*!40000 ALTER TABLE `base_appoption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_basecode`
--

DROP TABLE IF EXISTS `base_basecode`;
CREATE TABLE `base_basecode` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `content` varchar(30) NOT NULL,
  `content_class` int(11) default NULL,
  `display` varchar(30) default NULL,
  `value` varchar(30) NOT NULL,
  `remark` varchar(200) default NULL,
  `is_add` varchar(4) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3847 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_basecode`
--

LOCK TABLES `base_basecode` WRITE;
/*!40000 ALTER TABLE `base_basecode` DISABLE KEYS */;
INSERT INTO `base_basecode` VALUES (3835,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Simplified Chinese','zh-cn',NULL,NULL),(3836,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'English','en',NULL,NULL),(3837,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Spanish','es',NULL,NULL),(3838,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Traditional Chinese','zh-tw',NULL,NULL),(3839,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Polish','pl',NULL,NULL),(3840,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'French','fr',NULL,NULL),(3841,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Arabic','ar',NULL,NULL),(3842,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Vietnamese','vi',NULL,NULL),(3843,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Thai','th',NULL,NULL),(3844,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Russian','ru',NULL,NULL),(3845,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Portuguese','pt',NULL,NULL),(3846,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Italian','it',NULL,NULL);
/*!40000 ALTER TABLE `base_basecode` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_datatranslation`
--

DROP TABLE IF EXISTS `base_datatranslation`;
CREATE TABLE `base_datatranslation` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `content_type_id` int(11) default NULL,
  `property` varchar(100) NOT NULL,
  `language` varchar(10) NOT NULL,
  `value` varchar(200) NOT NULL,
  `display` varchar(400) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `base_datatranslation_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=17 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_datatranslation`
--

LOCK TABLES `base_datatranslation` WRITE;
/*!40000 ALTER TABLE `base_datatranslation` DISABLE KEYS */;
INSERT INTO `base_datatranslation` VALUES (1,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','worktable','worktable'),(2,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','dbapp','dbapp'),(3,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','auth','auth'),(4,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','django_extensions','django_extensions'),(5,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Simplified Chinese','Simplified Chinese'),(6,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','English','English'),(7,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Spanish','Spanish'),(8,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Traditional Chinese','Traditional Chinese'),(9,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Polish','Polish'),(10,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','French','French'),(11,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Arabic','Arabic'),(12,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Vietnamese','Vietnamese'),(13,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Thai','Thai'),(14,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Russian','Russian'),(15,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Portuguese','Portuguese'),(16,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Italian','Italian');
/*!40000 ALTER TABLE `base_datatranslation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_operatortemplate`
--

DROP TABLE IF EXISTS `base_operatortemplate`;
CREATE TABLE `base_operatortemplate` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  `template1` longtext,
  `finger_id` smallint(6) NOT NULL,
  `valid` smallint(6) NOT NULL,
  `fpversion` varchar(10) NOT NULL,
  `bio_type` smallint(6) NOT NULL,
  `utime` datetime default NULL,
  `bitmap_picture` longtext,
  `bitmap_picture2` longtext,
  `bitmap_picture3` longtext,
  `bitmap_picture4` longtext,
  `use_type` smallint(6) default NULL,
  `template2` longtext,
  `template3` longtext,
  `template_flag` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`finger_id`,`fpversion`),
  KEY `base_operatortemplate_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_operatortemplate`
--

LOCK TABLES `base_operatortemplate` WRITE;
/*!40000 ALTER TABLE `base_operatortemplate` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_operatortemplate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_option`
--

DROP TABLE IF EXISTS `base_option`;
CREATE TABLE `base_option` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(30) NOT NULL,
  `app_label` varchar(30) NOT NULL,
  `catalog` varchar(30) NOT NULL,
  `group` varchar(30) NOT NULL,
  `widget` varchar(400) NOT NULL,
  `required` tinyint(1) NOT NULL,
  `validator` varchar(400) NOT NULL,
  `verbose_name` varchar(80) NOT NULL,
  `help_text` varchar(160) NOT NULL,
  `visible` tinyint(1) NOT NULL,
  `default` varchar(100) NOT NULL,
  `read_only` tinyint(1) NOT NULL,
  `for_personal` tinyint(1) NOT NULL,
  `type` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=20 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_option`
--

LOCK TABLES `base_option` WRITE;
/*!40000 ALTER TABLE `base_option` DISABLE KEYS */;
INSERT INTO `base_option` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'date_format','base','2','','',0,'','Date Format','',1,'%Y-%m-%d',0,1,'CharField'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'time_format','base','2','','',0,'','Time Format','',1,'%H:%M:%S',0,1,'CharField'),(3,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'datetime_format','base','2','','',0,'','Datetime Format','',1,'%Y-%m-%d %H:%M:%S',0,1,'CharField'),(4,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'shortdate_format','base','2','','',0,'','Shortdate format','',1,'%y-%m-%d',0,1,'CharField'),(5,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'shortdatetime_format','base','2','','',0,'','Shortdatetime Format','',1,'%y-%m-%d %H:%M',0,1,'CharField'),(6,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'language','base','2','','',0,'','语言','',1,'en',0,1,'CharField'),(7,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'base_default_page','base','2','','',0,'','System Default Page','',0,'data/auth/User/',0,1,'CharField'),(8,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'site_default_page','base','2','','',0,'','System Default Page','',0,'data/worktable/',0,1,'CharField'),(9,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'site_device_page','base','2','','',0,'','Device List Page','',0,'data/iclock/device/',0,1,'CharField'),(10,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'backup_sched','base','1','','',0,'','备份时间','',1,'',0,1,'CharField'),(11,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'max_photo_width','dbapp','2','','',0,'','Maximum Image Width','',1,'800',0,1,'CharField'),(12,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'theme','dbapp','2','','',0,'','Style','',1,'flat',0,1,'CharField'),(13,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'personnel_default_page','personnel','2','','',0,'','Default access control page','',0,'data/personnel/Employee/',0,1,'CharField'),(14,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'iclock_default_page','iclock','2','','',0,'','Default access control page','',0,'data/iclock/device/',0,1,'CharField'),(15,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'att_default_page','att','2','','',0,'','default access control page','',0,'data/att/EmpSpecDay/',0,1,'CharField'),(16,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'iaccess_default_page','iaccess','2','','',0,'','default access control page','',0,'iaccess/RTMonitorPage/',0,1,'CharField'),(17,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'elevator_default_page','elevator','2','','',0,'','Default Page of Elevator Control System','',0,'elevator/FloorMngPage/',0,1,'CharField'),(18,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'video_default_page','video','2','','',0,'','Default page of Video','',0,'video/VideoPreviewPage/',0,1,'CharField'),(19,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'visitor_default_page','visitor','2','','',0,'','Visitors default Page','',0,'data/visitor/VisVisitor/',0,1,'CharField');
/*!40000 ALTER TABLE `base_option` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_personaloption`
--

DROP TABLE IF EXISTS `base_personaloption`;
CREATE TABLE `base_personaloption` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `option_id` int(11) NOT NULL,
  `value` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `option_id` (`option_id`,`user_id`),
  KEY `base_personaloption_option_id` (`option_id`),
  KEY `base_personaloption_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_personaloption`
--

LOCK TABLES `base_personaloption` WRITE;
/*!40000 ALTER TABLE `base_personaloption` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_personaloption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_strresource`
--

DROP TABLE IF EXISTS `base_strresource`;
CREATE TABLE `base_strresource` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `app` varchar(20) default NULL,
  `str` varchar(400) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_strresource`
--

LOCK TABLES `base_strresource` WRITE;
/*!40000 ALTER TABLE `base_strresource` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_strresource` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_strtranslation`
--

DROP TABLE IF EXISTS `base_strtranslation`;
CREATE TABLE `base_strtranslation` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `str_id` int(11) NOT NULL,
  `language` varchar(10) NOT NULL,
  `display` varchar(400) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `base_strtranslation_str_id` (`str_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_strtranslation`
--

LOCK TABLES `base_strtranslation` WRITE;
/*!40000 ALTER TABLE `base_strtranslation` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_strtranslation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_systemoption`
--

DROP TABLE IF EXISTS `base_systemoption`;
CREATE TABLE `base_systemoption` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `option_id` int(11) NOT NULL,
  `value` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `base_systemoption_option_id` (`option_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_systemoption`
--

LOCK TABLES `base_systemoption` WRITE;
/*!40000 ALTER TABLE `base_systemoption` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_systemoption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `checkexact`
--

DROP TABLE IF EXISTS `checkexact`;
CREATE TABLE `checkexact` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `CHECKTIME` datetime NOT NULL,
  `CHECKTYPE` varchar(5) NOT NULL,
  `ISADD` smallint(6) default NULL,
  `YUYIN` varchar(100) default NULL,
  `ISMODIFY` smallint(6) default NULL,
  `ISDELETE` smallint(6) default NULL,
  `INCOUNT` smallint(6) default NULL,
  `ISCOUNT` smallint(6) default NULL,
  `MODIFYBY` varchar(20) default NULL,
  `DATE` datetime default NULL,
  `audit_status` smallint(6) default NULL,
  `audit_reason` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  KEY `checkexact_UserID` (`UserID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `checkexact`
--

LOCK TABLES `checkexact` WRITE;
/*!40000 ALTER TABLE `checkexact` DISABLE KEYS */;
/*!40000 ALTER TABLE `checkexact` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `checkinout`
--

DROP TABLE IF EXISTS `checkinout`;
CREATE TABLE `checkinout` (
  `id` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `checktime` datetime NOT NULL,
  `checktype` varchar(5) NOT NULL,
  `verifycode` int(11) NOT NULL,
  `SN` int(11) default NULL,
  `sensorid` varchar(5) default NULL,
  `WorkCode` varchar(20) default NULL,
  `Reserved` varchar(20) default NULL,
  `sn_name` varchar(40) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `userid` (`userid`,`checktime`),
  KEY `checkinout_userid` (`userid`),
  KEY `checkinout_SN` (`SN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `checkinout`
--

LOCK TABLES `checkinout` WRITE;
/*!40000 ALTER TABLE `checkinout` DISABLE KEYS */;
/*!40000 ALTER TABLE `checkinout` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dbapp_viewmodel`
--

DROP TABLE IF EXISTS `dbapp_viewmodel`;
CREATE TABLE `dbapp_viewmodel` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `model_id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `info` longtext NOT NULL,
  `viewtype` varchar(20) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `dbapp_viewmodel_model_id` (`model_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `dbapp_viewmodel`
--

LOCK TABLES `dbapp_viewmodel` WRITE;
/*!40000 ALTER TABLE `dbapp_viewmodel` DISABLE KEYS */;
/*!40000 ALTER TABLE `dbapp_viewmodel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dbbackuplog`
--

DROP TABLE IF EXISTS `dbbackuplog`;
CREATE TABLE `dbbackuplog` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  `starttime` datetime default NULL,
  `imflag` tinyint(1) NOT NULL,
  `successflag` varchar(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `dbbackuplog_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `dbbackuplog`
--

LOCK TABLES `dbbackuplog` WRITE;
/*!40000 ALTER TABLE `dbbackuplog` DISABLE KEYS */;
/*!40000 ALTER TABLE `dbbackuplog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `DeptID` int(11) NOT NULL auto_increment,
  `DeptName` varchar(100) NOT NULL,
  `code` varchar(100) NOT NULL,
  `supdeptid` int(11) default NULL,
  `type` varchar(10) NOT NULL,
  `invalidate` date default NULL,
  PRIMARY KEY  (`DeptID`),
  KEY `departments_supdeptid` (`supdeptid`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
INSERT INTO `departments` VALUES (NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,1,'Department Name','1',NULL,'dept',NULL);
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deptadmin`
--

DROP TABLE IF EXISTS `deptadmin`;
CREATE TABLE `deptadmin` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `dept_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `deptadmin_user_id` (`user_id`),
  KEY `deptadmin_dept_id` (`dept_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `deptadmin`
--

LOCK TABLES `deptadmin` WRITE;
/*!40000 ALTER TABLE `deptadmin` DISABLE KEYS */;
/*!40000 ALTER TABLE `deptadmin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devcmds`
--

DROP TABLE IF EXISTS `devcmds`;
CREATE TABLE `devcmds` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `SN_id` int(11) default NULL,
  `CmdOperate_id` int(11) default NULL,
  `CmdContent` longtext NOT NULL,
  `CmdCommitTime` datetime NOT NULL,
  `CmdTransTime` datetime default NULL,
  `CmdOverTime` datetime default NULL,
  `CmdReturn` int(11) default NULL,
  `CmdReturnContent` longtext,
  `CmdImmediately` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `devcmds_SN_id` (`SN_id`),
  KEY `devcmds_CmdOperate_id` (`CmdOperate_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `devcmds`
--

LOCK TABLES `devcmds` WRITE;
/*!40000 ALTER TABLE `devcmds` DISABLE KEYS */;
/*!40000 ALTER TABLE `devcmds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devcmds_bak`
--

DROP TABLE IF EXISTS `devcmds_bak`;
CREATE TABLE `devcmds_bak` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `SN_id` int(11) default NULL,
  `CmdOperate_id` int(11) default NULL,
  `CmdContent` longtext NOT NULL,
  `CmdCommitTime` datetime NOT NULL,
  `CmdTransTime` datetime default NULL,
  `CmdOverTime` datetime default NULL,
  `CmdReturn` int(11) default NULL,
  `CmdReturnContent` longtext,
  `CmdImmediately` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `devcmds_bak_SN_id` (`SN_id`),
  KEY `devcmds_bak_CmdOperate_id` (`CmdOperate_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `devcmds_bak`
--

LOCK TABLES `devcmds_bak` WRITE;
/*!40000 ALTER TABLE `devcmds_bak` DISABLE KEYS */;
/*!40000 ALTER TABLE `devcmds_bak` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devlog`
--

DROP TABLE IF EXISTS `devlog`;
CREATE TABLE `devlog` (
  `id` int(11) NOT NULL auto_increment,
  `SN_id` int(11) NOT NULL,
  `OP` varchar(40) NOT NULL,
  `Object` varchar(80) default NULL,
  `Cnt` int(11) NOT NULL,
  `ECnt` int(11) NOT NULL,
  `OpTime` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `devlog_SN_id` (`SN_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `devlog`
--

LOCK TABLES `devlog` WRITE;
/*!40000 ALTER TABLE `devlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `devlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=92 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'session','sessions','session'),(2,'permission','auth','permission'),(3,'Role','auth','group'),(4,'User','auth','user'),(5,'message','auth','message'),(6,'content type','contenttypes','contenttype'),(7,'Log Events','base','logentry'),(8,'Added data','base','additiondata'),(9,'Translated to data','base','datatranslation'),(10,'Translated to character string resource','base','strtranslation'),(11,'str resource','base','strresource'),(12,'Basic code table','base','basecode'),(13,'Settings','base','option'),(14,'System Parameter','base','systemoption'),(15,'System Parameter','base','appoption'),(16,'Personal option','base','personaloption'),(17,'user fingerprint','base','operatortemplate'),(18,'Database Management','dbapp','dbbackuplog'),(19,'view model','dbapp','viewmodel'),(20,'Department','personnel','department'),(21,'Multi-Card Opening Personnel Groups','personnel','accmorecardempgroup'),(22,'Area Setting','personnel','area'),(23,'Personnel','personnel','employee'),(24,'Reports','personnel','empitemdefine'),(25,'Departure','personnel','leavelog'),(26,'Card type','personnel','cardtype'),(27,'Issue Card','personnel','issuecard'),(28,'Transfer','personnel','empchange'),(29,'Notice type','worktable','msgtype'),(30,'System reminder setting','worktable','groupmsg'),(31,'Confirm user information','worktable','usrmsg'),(32,'Release notice','worktable','instantmsg'),(33,'Daylight Saving Time','iclock','dstime'),(34,'Device','iclock','device'),(35,'Command details','iclock','operatecmd'),(36,'Server Sent Commands','iclock','devcmd'),(37,'Fingerprint','iclock','template'),(38,'AC log','iclock','transaction'),(39,'Device operation log','iclock','oplog'),(40,'Device communication log','iclock','devlog'),(41,'Failed Commands For Searching','iclock','devcmdbak'),(42,'Department Management','iclock','deptadmin'),(43,'Area Management','iclock','areaadmin'),(44,'test data','iclock','testdata'),(45,'Holiday','att','holiday'),(46,'TimeTable','att','schclass'),(47,'Shift','att','num_run'),(48,'Details','att','num_run_deil'),(49,'Temporary schedule','att','user_temp_sch'),(50,'Schedule','att','user_of_run'),(51,'Type','att','leaveclass'),(52,'Exception','att','empspecday'),(53,'Statistic table','att','leaveclass1'),(54,'Parameter','att','attparam'),(55,'user used s classes','att','userusedsclasses'),(56,'att calc log','att','attcalclog'),(57,'att exception','att','attexception'),(58,'Log result','att','attrecabnormite'),(59,'Daily detail','att','attshifts'),(60,'Report','att','attreport'),(61,'Append log','att','checkexact'),(62,'Reschedule','att','setuseratt'),(63,'wait for process data','att','waitforprocessdata'),(64,'加班单','att','overtime'),(65,'Time Zones','iaccess','acctimeseg'),(66,'Map','iaccess','accmap'),(67,'Wiegand Card Format','iaccess','accwiegandfmt'),(68,'Door','iaccess','accdoor'),(69,'Door Coordinates','iaccess','accmapdoorpos'),(70,'Access control device extension parameter','iaccess','accdevice'),(71,'Real Time Monitoring Events','iaccess','accrtmonitor'),(72,'Linkage Settings','iaccess','acclinkageio'),(73,'First-Card Normal Open Settings','iaccess','accfirstopen'),(74,'Multi-Card Opening Settings','iaccess','accmorecardset'),(75,'Multi-Card Opening Group','iaccess','accmorecardgroup'),(76,'Anti-Passback Settings','iaccess','accantiback'),(77,'Interlock Settings','iaccess','accinterlock'),(78,'Holidays','iaccess','accholidays'),(79,'Access Levels','iaccess','acclevelset'),(80,'全局反潜组设置','iaccess','accglobalapbgroup'),(81,'全局反潜设置','iaccess','accglobalapb'),(82,'Reader','iaccess','accreader'),(83,'Auxiliary Point','iaccess','auxiliary'),(84,'邮件','iaccess','emailrecord'),(85,'Video Channel','video','vidchannel'),(86,'VideoMapChannelPos','video','videomapchannelpos'),(87,'Add Reason','visitor','visreason'),(88,'Reservation Manage','visitor','visreservation'),(89,'Add Entry/Exit','visitor','visplace'),(90,'Visitor Manage','visitor','visvisitor'),(91,'Visitor History','visitor','visreport');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY  (`session_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('32d24aaa39e60002c378f4e56dfe0bfd','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-06 16:16:38'),('9e3f86c095c86e98a6130c7a5a322a03','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-14 14:03:25'),('c573af0c21f4647b2f6140ea037498a4','Z0FKOWNRRW9WUTFmWVhWMGFGOTFjMlZ5WDJsa2NRS0tBUUZWRWw5aGRYUm9YM1Z6WlhKZlltRmph\nMlZ1WkhFRFZTbGthbUZ1WjI4dQpZMjl1ZEhKcFlpNWhkWFJvTG1KaFkydGxibVJ6TGsxdlpHVnNR\nbUZqYTJWdVpIRUVWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoxYzQ3\nMGQyYWUyZTliZTkzOWMxNjhkOTJhMDkxNDk0Nw==\n','2025-10-06 16:15:30'),('0be8b36658ece604ee2a02fe12700237','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-07 09:23:53'),('6a4324a718c4ffa35bf3020e18dc5ad3','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-09 09:04:33'),('fbebb961090017f70c240737e04e0295','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-16 12:24:18'),('494cb880d0674cdea5de60cbda61510b','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-10 09:01:43'),('bc60db741e8186675831bd22d649e9dc','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-11-10 12:37:31'),('b4b8fe58434fe17f4cc44bfb1b1acdaf','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-20 10:29:45'),('e32bf4531ba8adef8d206d540ac3bbe3','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-17 09:39:00'),('173141e305eb72d93430baa52d72205b','Z0FKOWNRRW9WUTFmWVhWMGFGOTFjMlZ5WDJsa2NRS0tBUUZWRWw5aGRYUm9YM1Z6WlhKZlltRmph\nMlZ1WkhFRFZTbGthbUZ1WjI4dQpZMjl1ZEhKcFlpNWhkWFJvTG1KaFkydGxibVJ6TGsxdlpHVnNR\nbUZqYTJWdVpIRUVWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoxYzQ3\nMGQyYWUyZTliZTkzOWMxNjhkOTJhMDkxNDk0Nw==\n','2025-10-16 15:58:28');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `empitemdefine`
--

DROP TABLE IF EXISTS `empitemdefine`;
CREATE TABLE `empitemdefine` (
  `ItemName` varchar(100) NOT NULL,
  `ItemType` varchar(20) default NULL,
  `Author_id` int(11) NOT NULL,
  `ItemValue` longtext,
  `Published` smallint(6) default NULL,
  PRIMARY KEY  (`ItemName`),
  KEY `empitemdefine_Author_id` (`Author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `empitemdefine`
--

LOCK TABLES `empitemdefine` WRITE;
/*!40000 ALTER TABLE `empitemdefine` DISABLE KEYS */;
/*!40000 ALTER TABLE `empitemdefine` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `holidays`
--

DROP TABLE IF EXISTS `holidays`;
CREATE TABLE `holidays` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `HolidayID` int(11) NOT NULL auto_increment,
  `HolidayName` varchar(20) NOT NULL,
  `HolidayYear` smallint(6) default NULL,
  `HolidayMonth` smallint(6) default NULL,
  `HolidayDay` smallint(6) default NULL,
  `StartTime` date NOT NULL,
  `Duration` smallint(6) NOT NULL,
  `IsCycle` smallint(6) NOT NULL,
  `HolidayType` smallint(6) default NULL,
  `XINBIE` varchar(4) default NULL,
  `MINZU` varchar(50) default NULL,
  PRIMARY KEY  (`HolidayID`),
  UNIQUE KEY `HolidayName` (`HolidayName`,`StartTime`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `holidays`
--

LOCK TABLES `holidays` WRITE;
/*!40000 ALTER TABLE `holidays` DISABLE KEYS */;
INSERT INTO `holidays` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'New Year’s Day',2010,1,1,'2010-01-01',3,1,NULL,NULL,NULL),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,2,'National Day',2010,10,1,'2010-10-01',7,1,NULL,NULL,NULL);
/*!40000 ALTER TABLE `holidays` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock`
--

DROP TABLE IF EXISTS `iclock`;
CREATE TABLE `iclock` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `sn` varchar(50) default NULL,
  `device_brand` int(11) NOT NULL,
  `device_type` int(11) NOT NULL,
  `last_activity` datetime default NULL,
  `trans_times` varchar(50) default NULL,
  `TransInterval` int(11) default NULL,
  `log_stamp` varchar(20) default NULL,
  `oplog_stamp` varchar(20) default NULL,
  `photo_stamp` varchar(20) default NULL,
  `alias` varchar(20) NOT NULL,
  `UpdateDB` varchar(10) default NULL,
  `fw_version` varchar(50) default NULL,
  `device_name` varchar(30) default NULL,
  `fp_count` int(11) default NULL,
  `transaction_count` int(11) default NULL,
  `user_count` int(11) default NULL,
  `main_time` varchar(20) default NULL,
  `max_user_count` int(11) default NULL,
  `max_finger_count` int(11) default NULL,
  `max_attlog_count` int(11) default NULL,
  `alg_ver` varchar(30) default NULL,
  `flash_size` varchar(10) default NULL,
  `free_flash_size` varchar(10) default NULL,
  `language` varchar(30) default NULL,
  `lng_encode` varchar(10) default NULL,
  `volume` varchar(10) default NULL,
  `dt_fmt` varchar(10) default NULL,
  `is_tft` varchar(5) default NULL,
  `platform` varchar(20) default NULL,
  `brightness` varchar(5) default NULL,
  `oem_vendor` varchar(30) default NULL,
  `city` varchar(50) default NULL,
  `AccFun` smallint(6) NOT NULL,
  `TZAdj` smallint(6) default NULL,
  `comm_type` smallint(6) NOT NULL,
  `agent_ipaddress` varchar(20) default NULL,
  `ipaddress` char(15) default NULL,
  `ip_port` int(11) default NULL,
  `subnet_mask` char(15) default NULL,
  `gateway` char(15) default NULL,
  `com_port` smallint(6) default NULL,
  `baudrate` smallint(6) default NULL,
  `com_address` smallint(6) default NULL,
  `area_id` int(11) default NULL,
  `comm_pwd` varchar(32) default NULL,
  `video_channel_count` int(11) default NULL,
  `acpanel_type` int(11) default NULL,
  `sync_time` tinyint(1) NOT NULL,
  `four_to_two` tinyint(1) NOT NULL,
  `video_login` varchar(20) default NULL,
  `fp_mthreshold` int(11) default NULL,
  `Fpversion` varchar(10) default NULL,
  `enabled` tinyint(1) NOT NULL,
  `max_comm_size` int(11) default NULL,
  `max_comm_count` int(11) default NULL,
  `realtime` tinyint(1) NOT NULL,
  `delay` int(11) default NULL,
  `encrypt` tinyint(1) NOT NULL,
  `dstime_id` int(11) default NULL,
  `is_elevator_device` tinyint(1) NOT NULL,
  `ele_extboard_count` smallint(6) default NULL,
  `relay_per_board` smallint(6) default NULL,
  PRIMARY KEY  (`id`),
  KEY `iclock_area_id` (`area_id`),
  KEY `iclock_dstime_id` (`dstime_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock`
--

LOCK TABLES `iclock` WRITE;
/*!40000 ALTER TABLE `iclock` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_dstime`
--

DROP TABLE IF EXISTS `iclock_dstime`;
CREATE TABLE `iclock_dstime` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `dst_name` varchar(20) NOT NULL,
  `mode` smallint(6) default NULL,
  `start_time` varchar(20) default NULL,
  `end_time` varchar(20) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `dst_name` (`dst_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_dstime`
--

LOCK TABLES `iclock_dstime` WRITE;
/*!40000 ALTER TABLE `iclock_dstime` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_dstime` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_oplog`
--

DROP TABLE IF EXISTS `iclock_oplog`;
CREATE TABLE `iclock_oplog` (
  `id` int(11) NOT NULL auto_increment,
  `SN` int(11) default NULL,
  `admin` int(11) NOT NULL,
  `OP` smallint(6) NOT NULL,
  `OPTime` datetime NOT NULL,
  `Object` int(11) default NULL,
  `Param1` int(11) default NULL,
  `Param2` int(11) default NULL,
  `Param3` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `SN` (`SN`,`OPTime`),
  KEY `iclock_oplog_SN` (`SN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_oplog`
--

LOCK TABLES `iclock_oplog` WRITE;
/*!40000 ALTER TABLE `iclock_oplog` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_oplog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_testdata`
--

DROP TABLE IF EXISTS `iclock_testdata`;
CREATE TABLE `iclock_testdata` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `dept_id` int(11) NOT NULL,
  `area_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `iclock_testdata_dept_id` (`dept_id`),
  KEY `iclock_testdata_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_testdata`
--

LOCK TABLES `iclock_testdata` WRITE;
/*!40000 ALTER TABLE `iclock_testdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_testdata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_testdata_admin_area`
--

DROP TABLE IF EXISTS `iclock_testdata_admin_area`;
CREATE TABLE `iclock_testdata_admin_area` (
  `id` int(11) NOT NULL auto_increment,
  `testdata_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `testdata_id` (`testdata_id`,`area_id`),
  KEY `iclock_testdata_admin_area_testdata_id` (`testdata_id`),
  KEY `iclock_testdata_admin_area_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_testdata_admin_area`
--

LOCK TABLES `iclock_testdata_admin_area` WRITE;
/*!40000 ALTER TABLE `iclock_testdata_admin_area` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_testdata_admin_area` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_testdata_admin_dept`
--

DROP TABLE IF EXISTS `iclock_testdata_admin_dept`;
CREATE TABLE `iclock_testdata_admin_dept` (
  `id` int(11) NOT NULL auto_increment,
  `testdata_id` int(11) NOT NULL,
  `department_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `testdata_id` (`testdata_id`,`department_id`),
  KEY `iclock_testdata_admin_dept_testdata_id` (`testdata_id`),
  KEY `iclock_testdata_admin_dept_department_id` (`department_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_testdata_admin_dept`
--

LOCK TABLES `iclock_testdata_admin_dept` WRITE;
/*!40000 ALTER TABLE `iclock_testdata_admin_dept` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_testdata_admin_dept` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leaveclass`
--

DROP TABLE IF EXISTS `leaveclass`;
CREATE TABLE `leaveclass` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `LeaveID` int(11) NOT NULL auto_increment,
  `LeaveName` varchar(20) NOT NULL,
  `MinUnit` double NOT NULL,
  `Unit` smallint(6) NOT NULL,
  `RemaindProc` smallint(6) NOT NULL,
  `RemaindCount` smallint(6) NOT NULL,
  `ReportSymbol` varchar(4) NOT NULL,
  `Deduct` double default NULL,
  `Color` int(11) NOT NULL,
  `Classify` smallint(6) NOT NULL,
  `clearance` smallint(6) NOT NULL,
  `LeaveType` smallint(6) NOT NULL,
  PRIMARY KEY  (`LeaveID`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `leaveclass`
--

LOCK TABLES `leaveclass` WRITE;
/*!40000 ALTER TABLE `leaveclass` DISABLE KEYS */;
INSERT INTO `leaveclass` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'Sick',1,1,1,1,'B',0,3398744,0,0,1),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,2,'Personal',0.5,1,1,1,'G',0,16715535,0,0,2),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,3,'Maternity',0.5,1,1,1,'C',0,16715535,0,0,3),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,4,'Compassionate',1,1,1,1,'T',0,16744576,0,0,4),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,5,'Annual',1,1,1,1,'S',0,8421631,0,0,5),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,6,'Business Trip',1,1,1,1,'W',0,16715535,0,0,6);
/*!40000 ALTER TABLE `leaveclass` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leaveclass1`
--

DROP TABLE IF EXISTS `leaveclass1`;
CREATE TABLE `leaveclass1` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `LeaveID` int(11) NOT NULL auto_increment,
  `LeaveName` varchar(20) NOT NULL,
  `MinUnit` double NOT NULL,
  `Unit` smallint(6) NOT NULL,
  `RemaindProc` smallint(6) NOT NULL,
  `RemaindCount` smallint(6) NOT NULL,
  `ReportSymbol` varchar(4) NOT NULL,
  `Deduct` double NOT NULL,
  `Color` int(11) NOT NULL,
  `Classify` smallint(6) NOT NULL,
  `LeaveType` smallint(6) NOT NULL,
  `Calc` longtext,
  PRIMARY KEY  (`LeaveID`)
) ENGINE=MyISAM AUTO_INCREMENT=1010 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `leaveclass1`
--

LOCK TABLES `leaveclass1` WRITE;
/*!40000 ALTER TABLE `leaveclass1` DISABLE KEYS */;
INSERT INTO `leaveclass1` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1000,'应到/实到',0.5,3,1,0,' ',0,0,0,3,NULL),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1001,'迟到',10,2,2,1,'>',0,0,0,3,'AttItem(minLater)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1002,'早退',10,2,2,1,'<',0,0,0,3,'AttItem(minEarly)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1003,'请假',1,1,1,1,'V',0,0,0,3,'if((AttItem(LeaveType1)>0) and (AttItem(LeaveType1)<999), \"AttItem(LeaveTime1), \"0)+if((AttItem(LeaveType2)>0) and (AttItem(LeaveType2)<999), \"AttItem(LeaveTime2), \"0)+if((AttItem(LeaveType3)>0) and (AttItem(LeaveType3)<999), \"AttItem(LeaveTime3), \"0)+if((AttItem(LeaveType4)>0) and (AttItem(LeaveType4)<999), \"AttItem(LeaveTime4), \"0)+if((AttItem(LeaveType5)>0) and (AttItem(LeaveType5)<999), \"AttItem(LeaveTime5), \"0)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1004,'旷工',0.5,3,1,0,'A',0,0,0,3,'AttItem(MinAbsent)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1005,'加班',1,1,1,1,'+',0,0,0,3,'AttItem(MinOverTime)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1008,'未签到',1,4,2,1,'[',0,0,0,2,'If(AttItem(CheckIn)\": null, \"If(AttItem(OnDuty)\": null, \"0, \"if(((AttItem(LeaveStart1)\": null) or (AttItem(LeaveStart1)>AttItem(OnDuty))) and AttItem(DutyOn), \"1, \"0)), \"0)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1009,'未签退',1,4,2,1,']',0,0,0,2,'If(AttItem(CheckOut)\": null, \"If(AttItem(OffDuty)\": null, \"0, \"if((AttItem(LeaveEnd1)\": null) or (AttItem(LeaveEnd1)<AttItem(OffDuty)), \"if((AttItem(LeaveEnd2)\": null) or (AttItem(LeaveEnd2)<AttItem(OffDuty)), \"if(((AttItem(LeaveEnd3)\": null) or (AttItem(LeaveEnd3)<AttItem(OffDuty))) and AttItem(DutyOff), \"1, \"0), \"0), \"0)), \"0)');
/*!40000 ALTER TABLE `leaveclass1` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `num_run`
--

DROP TABLE IF EXISTS `num_run`;
CREATE TABLE `num_run` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `Num_runID` int(11) NOT NULL auto_increment,
  `OLDID` int(11) default NULL,
  `Name` varchar(30) NOT NULL,
  `StartDate` date default NULL,
  `EndDate` date default NULL,
  `Units` smallint(6) NOT NULL,
  `Cyle` smallint(6) NOT NULL,
  PRIMARY KEY  (`Num_runID`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `num_run`
--

LOCK TABLES `num_run` WRITE;
/*!40000 ALTER TABLE `num_run` DISABLE KEYS */;
INSERT INTO `num_run` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,-1,'Flexible shift','2025-10-06','2025-10-06',1,1);
/*!40000 ALTER TABLE `num_run` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `num_run_deil`
--

DROP TABLE IF EXISTS `num_run_deil`;
CREATE TABLE `num_run_deil` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `Num_runID` int(11) NOT NULL,
  `StartTime` time NOT NULL,
  `EndTime` time default NULL,
  `Sdays` smallint(6) NOT NULL,
  `Edays` smallint(6) default NULL,
  `SchclassID` int(11) default NULL,
  `OverTime` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `Num_runID` (`Num_runID`,`Sdays`,`StartTime`),
  KEY `num_run_deil_Num_runID` (`Num_runID`),
  KEY `num_run_deil_SchclassID` (`SchclassID`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `num_run_deil`
--

LOCK TABLES `num_run_deil` WRITE;
/*!40000 ALTER TABLE `num_run_deil` DISABLE KEYS */;
INSERT INTO `num_run_deil` VALUES (1,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',0,0,1,0),(2,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',1,1,1,0),(3,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',2,2,1,0),(4,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',3,3,1,0),(5,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',4,4,1,0),(6,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',5,5,1,0),(7,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',6,6,1,0);
/*!40000 ALTER TABLE `num_run_deil` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operatecmds`
--

DROP TABLE IF EXISTS `operatecmds`;
CREATE TABLE `operatecmds` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `Author_id` int(11) default NULL,
  `CmdContent` longtext NOT NULL,
  `CmdCommitTime` datetime NOT NULL,
  `commit_time` datetime default NULL,
  `CmdReturn` int(11) default NULL,
  `process_count` smallint(6) NOT NULL,
  `success_flag` smallint(6) NOT NULL,
  `receive_data` longtext,
  `cmm_type` smallint(6) NOT NULL,
  `cmm_system` smallint(6) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `operatecmds_Author_id` (`Author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `operatecmds`
--

LOCK TABLES `operatecmds` WRITE;
/*!40000 ALTER TABLE `operatecmds` DISABLE KEYS */;
/*!40000 ALTER TABLE `operatecmds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_area`
--

DROP TABLE IF EXISTS `personnel_area`;
CREATE TABLE `personnel_area` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `areaid` varchar(20) NOT NULL,
  `areaname` varchar(30) NOT NULL,
  `parent_id` int(11) default NULL,
  `remark` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  KEY `personnel_area_parent_id` (`parent_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_area`
--

LOCK TABLES `personnel_area` WRITE;
/*!40000 ALTER TABLE `personnel_area` DISABLE KEYS */;
INSERT INTO `personnel_area` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'1','Area Name',NULL,NULL);
/*!40000 ALTER TABLE `personnel_area` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_cardtype`
--

DROP TABLE IF EXISTS `personnel_cardtype`;
CREATE TABLE `personnel_cardtype` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `cardtypecode` varchar(20) NOT NULL,
  `cardtypename` varchar(50) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_cardtype`
--

LOCK TABLES `personnel_cardtype` WRITE;
/*!40000 ALTER TABLE `personnel_cardtype` DISABLE KEYS */;
INSERT INTO `personnel_cardtype` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'01','VIP card'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'02','Ordinary card');
/*!40000 ALTER TABLE `personnel_cardtype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_empchange`
--

DROP TABLE IF EXISTS `personnel_empchange`;
CREATE TABLE `personnel_empchange` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `changeno` int(11) NOT NULL auto_increment,
  `UserID_id` int(11) NOT NULL,
  `changedate` datetime default NULL,
  `changepostion` int(11) default NULL,
  `oldvalue` longtext,
  `newvalue` longtext,
  `changereason` varchar(200) default NULL,
  `isvalid` tinyint(1) NOT NULL,
  `approvalstatus` int(11) NOT NULL,
  `remark` varchar(200) default NULL,
  PRIMARY KEY  (`changeno`),
  KEY `personnel_empchange_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_empchange`
--

LOCK TABLES `personnel_empchange` WRITE;
/*!40000 ALTER TABLE `personnel_empchange` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_empchange` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_issuecard`
--

DROP TABLE IF EXISTS `personnel_issuecard`;
CREATE TABLE `personnel_issuecard` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) NOT NULL,
  `cardno` varchar(20) NOT NULL,
  `card_number` varchar(20) default NULL,
  `site_code` varchar(4) default NULL,
  `card_number_type` smallint(6) default NULL,
  `effectivenessdate` date default NULL,
  `isvalid` tinyint(1) NOT NULL,
  `cardpwd` varchar(20) default NULL,
  `failuredate` date default NULL,
  `cardstatus` varchar(20) NOT NULL,
  `issuedate` date default NULL,
  PRIMARY KEY  (`id`),
  KEY `personnel_issuecard_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_issuecard`
--

LOCK TABLES `personnel_issuecard` WRITE;
/*!40000 ALTER TABLE `personnel_issuecard` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_issuecard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_leavelog`
--

DROP TABLE IF EXISTS `personnel_leavelog`;
CREATE TABLE `personnel_leavelog` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) NOT NULL,
  `leavedate` date NOT NULL,
  `leavetype` int(11) NOT NULL,
  `reason` varchar(200) default NULL,
  `isReturnTools` tinyint(1) NOT NULL,
  `isReturnClothes` tinyint(1) NOT NULL,
  `isReturnCard` tinyint(1) NOT NULL,
  `isClassAtt` tinyint(1) NOT NULL,
  `isClassAccess` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `personnel_leavelog_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_leavelog`
--

LOCK TABLES `personnel_leavelog` WRITE;
/*!40000 ALTER TABLE `personnel_leavelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_leavelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schclass`
--

DROP TABLE IF EXISTS `schclass`;
CREATE TABLE `schclass` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `SchclassID` int(11) NOT NULL auto_increment,
  `SchName` varchar(20) NOT NULL,
  `StartTime` time NOT NULL,
  `EndTime` time NOT NULL,
  `LateMinutes` int(11) default NULL,
  `EarlyMinutes` int(11) default NULL,
  `CheckIn` smallint(6) NOT NULL,
  `CheckOut` smallint(6) NOT NULL,
  `CheckInTime1` time NOT NULL,
  `CheckInTime2` time NOT NULL,
  `CheckOutTime1` time NOT NULL,
  `CheckOutTime2` time NOT NULL,
  `Color` int(11) NOT NULL,
  `AutoBind` smallint(6) default NULL,
  `WorkDay` double default NULL,
  `IsCalcRest` int(11) default NULL,
  `StartRestTime` time default NULL,
  `EndRestTime` time default NULL,
  `StartRestTime1` time default NULL,
  `EndRestTime1` time default NULL,
  `shiftworktime` int(11) NOT NULL,
  `IsOverTime` smallint(6) NOT NULL,
  `OverTime` int(11) default NULL,
  PRIMARY KEY  (`SchclassID`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `schclass`
--

LOCK TABLES `schclass` WRITE;
/*!40000 ALTER TABLE `schclass` DISABLE KEYS */;
INSERT INTO `schclass` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'Flexible TimeTable','08:00:00','18:00:00',0,0,1,1,'00:01:00','23:00:00','01:00:00','23:59:00',16715535,1,1,0,NULL,NULL,NULL,NULL,480,1,0);
/*!40000 ALTER TABLE `schclass` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `setuseratt`
--

DROP TABLE IF EXISTS `setuseratt`;
CREATE TABLE `setuseratt` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) default NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `atttype` smallint(6) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `setuseratt_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `setuseratt`
--

LOCK TABLES `setuseratt` WRITE;
/*!40000 ALTER TABLE `setuseratt` DISABLE KEYS */;
/*!40000 ALTER TABLE `setuseratt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `template`
--

DROP TABLE IF EXISTS `template`;
CREATE TABLE `template` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `templateid` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `Template` longtext NOT NULL,
  `FingerID` smallint(6) NOT NULL,
  `Valid` smallint(6) NOT NULL,
  `Fpversion` varchar(10) NOT NULL,
  `bio_type` smallint(6) NOT NULL,
  `SN` int(11) default NULL,
  `UTime` datetime default NULL,
  `BITMAPPICTURE` longtext,
  `BITMAPPICTURE2` longtext,
  `BITMAPPICTURE3` longtext,
  `BITMAPPICTURE4` longtext,
  `USETYPE` smallint(6) default NULL,
  `Template2` longtext,
  `Template3` longtext,
  PRIMARY KEY  (`templateid`),
  UNIQUE KEY `userid` (`userid`,`FingerID`,`Fpversion`),
  KEY `template_userid` (`userid`),
  KEY `template_SN` (`SN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `template`
--

LOCK TABLES `template` WRITE;
/*!40000 ALTER TABLE `template` DISABLE KEYS */;
/*!40000 ALTER TABLE `template` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_of_run`
--

DROP TABLE IF EXISTS `user_of_run`;
CREATE TABLE `user_of_run` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `StartDate` date NOT NULL,
  `EndDate` date NOT NULL,
  `NUM_OF_RUN_ID` int(11) NOT NULL,
  `ISNOTOF_RUN` int(11) default NULL,
  `ORDER_RUN` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserID` (`UserID`,`NUM_OF_RUN_ID`,`StartDate`,`EndDate`),
  KEY `user_of_run_UserID` (`UserID`),
  KEY `user_of_run_NUM_OF_RUN_ID` (`NUM_OF_RUN_ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user_of_run`
--

LOCK TABLES `user_of_run` WRITE;
/*!40000 ALTER TABLE `user_of_run` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_of_run` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_speday`
--

DROP TABLE IF EXISTS `user_speday`;
CREATE TABLE `user_speday` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `StartSpecDay` datetime NOT NULL,
  `EndSpecDay` datetime default NULL,
  `DateID` int(11) NOT NULL,
  `YUANYING` varchar(100) default NULL,
  `Date` datetime default NULL,
  `audit_status` smallint(6) default NULL,
  `audit_reason` varchar(100) default NULL,
  `State` varchar(2) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserID` (`UserID`,`StartSpecDay`,`DateID`),
  KEY `user_speday_UserID` (`UserID`),
  KEY `user_speday_DateID` (`DateID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user_speday`
--

LOCK TABLES `user_speday` WRITE;
/*!40000 ALTER TABLE `user_speday` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_speday` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_temp_sch`
--

DROP TABLE IF EXISTS `user_temp_sch`;
CREATE TABLE `user_temp_sch` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `ComeTime` datetime NOT NULL,
  `LeaveTime` datetime NOT NULL,
  `OverTime` int(11) NOT NULL,
  `Type` smallint(6) default NULL,
  `Flag` smallint(6) default NULL,
  `SchClassID` int(11) default NULL,
  `WorkType` smallint(6) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserID` (`UserID`,`ComeTime`,`LeaveTime`),
  KEY `user_temp_sch_UserID` (`UserID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user_temp_sch`
--

LOCK TABLES `user_temp_sch` WRITE;
/*!40000 ALTER TABLE `user_temp_sch` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_temp_sch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userinfo`
--

DROP TABLE IF EXISTS `userinfo`;
CREATE TABLE `userinfo` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `userid` int(11) NOT NULL auto_increment,
  `badgenumber` varchar(20) NOT NULL,
  `defaultdeptid` int(11) default NULL,
  `name` varchar(24) default NULL,
  `lastname` varchar(20) default NULL,
  `Password` varchar(16) default NULL,
  `Card` varchar(20) NOT NULL,
  `card_number` varchar(20) default NULL,
  `site_code` varchar(4) default NULL,
  `card_number_type` smallint(6) default NULL,
  `Privilege` int(11) default NULL,
  `AccGroup` int(11) default NULL,
  `TimeZones` varchar(20) default NULL,
  `Gender` varchar(2) default NULL,
  `Birthday` date default NULL,
  `street` varchar(100) default NULL,
  `zip` varchar(6) default NULL,
  `ophone` varchar(20) default NULL,
  `FPHONE` varchar(20) default NULL,
  `pager` varchar(20) default NULL,
  `minzu` varchar(20) default NULL,
  `title` varchar(50) default NULL,
  `SSN` varchar(20) default NULL,
  `identitycard` varchar(20) default NULL,
  `UTime` datetime default NULL,
  `Hiredday` date default NULL,
  `VERIFICATIONMETHOD` smallint(6) default NULL,
  `State` varchar(50) default NULL,
  `City` varchar(50) default NULL,
  `Education` varchar(50) default NULL,
  `SECURITYFLAGS` smallint(6) default NULL,
  `ATT` tinyint(1) NOT NULL,
  `OverTime` tinyint(1) NOT NULL,
  `Holiday` tinyint(1) NOT NULL,
  `INLATE` smallint(6) default NULL,
  `OutEarly` smallint(6) default NULL,
  `Lunchduration` smallint(6) default NULL,
  `MVerifyPass` varchar(6) default NULL,
  `photo` varchar(200) default NULL,
  `SEP` smallint(6) default NULL,
  `OffDuty` smallint(6) default NULL,
  `DelTag` smallint(6) default NULL,
  `AutoSchPlan` smallint(6) default NULL,
  `MinAutoSchInterval` int(11) default NULL,
  `RegisterOT` int(11) default NULL,
  `morecard_group_id` int(11) default NULL,
  `set_valid_time` tinyint(1) NOT NULL,
  `acc_startdate` date default NULL,
  `acc_enddate` date default NULL,
  `acc_super_auth` smallint(6) default NULL,
  `ele_super_auth` smallint(6) default NULL,
  `delayed_door_open` tinyint(1) NOT NULL,
  `extend_time` smallint(6) default NULL,
  `birthplace` varchar(20) default NULL,
  `Political` varchar(20) default NULL,
  `contry` varchar(20) default NULL,
  `hiretype` int(11) default NULL,
  `email` varchar(50) default NULL,
  `firedate` date default NULL,
  `isatt` tinyint(1) NOT NULL,
  `homeaddress` varchar(100) default NULL,
  `emptype` int(11) default NULL,
  `bankcode1` varchar(50) default NULL,
  `bankcode2` varchar(50) default NULL,
  `isblacklist` int(11) default NULL,
  `selfpassword` varchar(20) default NULL,
  PRIMARY KEY  (`userid`),
  UNIQUE KEY `badgenumber` (`badgenumber`),
  KEY `userinfo_defaultdeptid` (`defaultdeptid`),
  KEY `userinfo_morecard_group_id` (`morecard_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `userinfo`
--

LOCK TABLES `userinfo` WRITE;
/*!40000 ALTER TABLE `userinfo` DISABLE KEYS */;
/*!40000 ALTER TABLE `userinfo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userinfo_attarea`
--

DROP TABLE IF EXISTS `userinfo_attarea`;
CREATE TABLE `userinfo_attarea` (
  `id` int(11) NOT NULL auto_increment,
  `employee_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `employee_id` (`employee_id`,`area_id`),
  KEY `userinfo_attarea_employee_id` (`employee_id`),
  KEY `userinfo_attarea_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `userinfo_attarea`
--

LOCK TABLES `userinfo_attarea` WRITE;
/*!40000 ALTER TABLE `userinfo_attarea` DISABLE KEYS */;
/*!40000 ALTER TABLE `userinfo_attarea` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `useruusedsclasses`
--

DROP TABLE IF EXISTS `useruusedsclasses`;
CREATE TABLE `useruusedsclasses` (
  `id` int(11) NOT NULL auto_increment,
  `UserId` int(11) NOT NULL,
  `SchId` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserId` (`UserId`,`SchId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `useruusedsclasses`
--

LOCK TABLES `useruusedsclasses` WRITE;
/*!40000 ALTER TABLE `useruusedsclasses` DISABLE KEYS */;
/*!40000 ALTER TABLE `useruusedsclasses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vid_channel`
--

DROP TABLE IF EXISTS `vid_channel`;
CREATE TABLE `vid_channel` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `channel_no` smallint(5) unsigned default NULL,
  `channel_name` varchar(30) default NULL,
  `enabled` tinyint(1) NOT NULL,
  `reader_id` int(11) default NULL,
  `map_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `vid_channel_device_id` (`device_id`),
  KEY `vid_channel_reader_id` (`reader_id`),
  KEY `vid_channel_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vid_channel`
--

LOCK TABLES `vid_channel` WRITE;
/*!40000 ALTER TABLE `vid_channel` DISABLE KEYS */;
/*!40000 ALTER TABLE `vid_channel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vid_mapchannelpos`
--

DROP TABLE IF EXISTS `vid_mapchannelpos`;
CREATE TABLE `vid_mapchannelpos` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `map_channel_id` int(11) default NULL,
  `map_id` int(11) default NULL,
  `width` double default NULL,
  `left` double default NULL,
  `top` double default NULL,
  PRIMARY KEY  (`id`),
  KEY `vid_mapchannelpos_map_channel_id` (`map_channel_id`),
  KEY `vid_mapchannelpos_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vid_mapchannelpos`
--

LOCK TABLES `vid_mapchannelpos` WRITE;
/*!40000 ALTER TABLE `vid_mapchannelpos` DISABLE KEYS */;
/*!40000 ALTER TABLE `vid_mapchannelpos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_place`
--

DROP TABLE IF EXISTS `vis_place`;
CREATE TABLE `vis_place` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `code` varchar(30) default NULL,
  `name` varchar(50) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_place`
--

LOCK TABLES `vis_place` WRITE;
/*!40000 ALTER TABLE `vis_place` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_place` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_reason`
--

DROP TABLE IF EXISTS `vis_reason`;
CREATE TABLE `vis_reason` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `code` varchar(30) default NULL,
  `reason` varchar(50) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `reason` (`reason`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_reason`
--

LOCK TABLES `vis_reason` WRITE;
/*!40000 ALTER TABLE `vis_reason` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_reason` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_report`
--

DROP TABLE IF EXISTS `vis_report`;
CREATE TABLE `vis_report` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `visited_pin` varchar(20) default NULL,
  `visited_firstname` varchar(24) default NULL,
  `visited_lastname` varchar(24) default NULL,
  `visited_dept` varchar(100) default NULL,
  `visited_phone` varchar(20) default NULL,
  `visitor_pin` varchar(9) default NULL,
  `visitor_firstname` varchar(24) default NULL,
  `visitor_lastname` varchar(24) default NULL,
  `gender` varchar(10) default NULL,
  `homeaddress` varchar(100) default NULL,
  `cert_type` varchar(50) default NULL,
  `cert_number` varchar(20) default NULL,
  `card` varchar(20) default NULL,
  `visitor_company` varchar(50) default NULL,
  `visit_reason` varchar(100) default NULL,
  `visitor_number` int(11) default NULL,
  `enter_time` datetime default NULL,
  `exit_time` datetime default NULL,
  `entrance` varchar(50) default NULL,
  `exit_place` varchar(50) default NULL,
  `visit_state` varchar(20) default NULL,
  `carried_goods` longtext,
  `photo` varchar(50) default NULL,
  `enter_photo` varchar(50) default NULL,
  `exit_photo` varchar(50) default NULL,
  `visitor_form` varchar(30) default NULL,
  `car_number` varchar(15) default NULL,
  `park_number` varchar(15) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_report`
--

LOCK TABLES `vis_report` WRITE;
/*!40000 ALTER TABLE `vis_report` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_reservation`
--

DROP TABLE IF EXISTS `vis_reservation`;
CREATE TABLE `vis_reservation` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `visited_emp_id` int(11) NOT NULL,
  `visitor_firstname` varchar(24) default NULL,
  `visitor_lastname` varchar(24) default NULL,
  `visitor_company` varchar(24) default NULL,
  `visit_reason_id` int(11) default NULL,
  `visit_date` date default NULL,
  `remark` varchar(200) default NULL,
  PRIMARY KEY  (`id`),
  KEY `vis_reservation_visited_emp_id` (`visited_emp_id`),
  KEY `vis_reservation_visit_reason_id` (`visit_reason_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_reservation`
--

LOCK TABLES `vis_reservation` WRITE;
/*!40000 ALTER TABLE `vis_reservation` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_reservation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_visitor`
--

DROP TABLE IF EXISTS `vis_visitor`;
CREATE TABLE `vis_visitor` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `visitor_id` int(11) default NULL,
  `cert_type` smallint(6) default NULL,
  `cert_number` varchar(20) default NULL,
  `visitor_company` varchar(24) default NULL,
  `visit_reason_id` int(11) default NULL,
  `visitor_number` int(11) default NULL,
  `visit_state` int(11) default NULL,
  `enter_time` datetime default NULL,
  `exit_time` datetime default NULL,
  `entrance_id` int(11) default NULL,
  `exit_place_id` int(11) default NULL,
  `cert_photo` longtext,
  `capture_photo` longtext,
  `car_number` varchar(15) default NULL,
  `park_number` varchar(15) default NULL,
  `carried_goods` longtext,
  `visitor_form` varchar(30) default NULL,
  `visited_emp_id` int(11) default NULL,
  `has_alarmed` tinyint(1) NOT NULL,
  `has_visited` tinyint(1) NOT NULL,
  `exit_registered` tinyint(1) NOT NULL,
  `return_card` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `vis_visitor_visitor_id` (`visitor_id`),
  KEY `vis_visitor_visit_reason_id` (`visit_reason_id`),
  KEY `vis_visitor_entrance_id` (`entrance_id`),
  KEY `vis_visitor_exit_place_id` (`exit_place_id`),
  KEY `vis_visitor_visited_emp_id` (`visited_emp_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_visitor`
--

LOCK TABLES `vis_visitor` WRITE;
/*!40000 ALTER TABLE `vis_visitor` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_visitor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_groupmsg`
--

DROP TABLE IF EXISTS `worktable_groupmsg`;
CREATE TABLE `worktable_groupmsg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `msgtype_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `worktable_groupmsg_msgtype_id` (`msgtype_id`),
  KEY `worktable_groupmsg_group_id` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_groupmsg`
--

LOCK TABLES `worktable_groupmsg` WRITE;
/*!40000 ALTER TABLE `worktable_groupmsg` DISABLE KEYS */;
/*!40000 ALTER TABLE `worktable_groupmsg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_instantmsg`
--

DROP TABLE IF EXISTS `worktable_instantmsg`;
CREATE TABLE `worktable_instantmsg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `monitor last time` datetime default NULL,
  `msgtype_id` int(11) NOT NULL,
  `content` longtext,
  PRIMARY KEY  (`id`),
  KEY `worktable_instantmsg_msgtype_id` (`msgtype_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_instantmsg`
--

LOCK TABLES `worktable_instantmsg` WRITE;
/*!40000 ALTER TABLE `worktable_instantmsg` DISABLE KEYS */;
/*!40000 ALTER TABLE `worktable_instantmsg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_msgtype`
--

DROP TABLE IF EXISTS `worktable_msgtype`;
CREATE TABLE `worktable_msgtype` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `msgtype_name` varchar(50) NOT NULL,
  `msgtype_value` varchar(20) NOT NULL,
  `msg_keep_time` int(11) NOT NULL,
  `msg_ahead_remind` int(11) NOT NULL,
  `type` varchar(2) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_msgtype`
--

LOCK TABLES `worktable_msgtype` WRITE;
/*!40000 ALTER TABLE `worktable_msgtype` DISABLE KEYS */;
INSERT INTO `worktable_msgtype` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'System','9',1,0,'-1'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'Attendance','8',1,0,'-1'),(3,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'Access Control','7',1,0,'-1'),(4,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'Personnel','6',1,0,'-1');
/*!40000 ALTER TABLE `worktable_msgtype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_usrmsg`
--

DROP TABLE IF EXISTS `worktable_usrmsg`;
CREATE TABLE `worktable_usrmsg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `user_id` int(11) default NULL,
  `msg_id` int(11) default NULL,
  `readtype` varchar(20) default NULL,
  PRIMARY KEY  (`id`),
  KEY `worktable_usrmsg_user_id` (`user_id`),
  KEY `worktable_usrmsg_msg_id` (`msg_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_usrmsg`
--

LOCK TABLES `worktable_usrmsg` WRITE;
/*!40000 ALTER TABLE `worktable_usrmsg` DISABLE KEYS */;
/*!40000 ALTER TABLE `worktable_usrmsg` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-18  5:45:46
