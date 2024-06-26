CREATE TABLE `scr_pharma` (
  `id` INT UNSIGNED AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `url` VARCHAR(255) NOT NULL,
  `category` VARCHAR(255) NOT NULL,
  `price` DECIMAL(10,2),
  `price_sale` DECIMAL(10,2),
  `brand` VARCHAR(255) NOT NULL,
  `timestamp` DATETIME NOT NULL,
  `spider_name` VARCHAR(255) NOT NULL,
  `code` VARCHAR(255),
  `price_benef` DECIMAL(10,2),
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_unique` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;