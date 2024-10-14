CREATE TABLE `scr_pharma` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `url` varchar(255) NOT NULL,
  `category` varchar(255) NOT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `price_sale` decimal(10,2) DEFAULT NULL,
  `brand` varchar(255) NOT NULL,
  `timestamp` datetime NOT NULL,
  `spider_name` varchar(255) NOT NULL,
  `code` varchar(255) DEFAULT NULL,
  `price_benef` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `url_index` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;