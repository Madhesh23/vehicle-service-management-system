-- Reference MySQL schema (app.py creates this automatically on first run).
CREATE DATABASE IF NOT EXISTS vehicle_service_db CHARACTER SET utf8mb4;
USE vehicle_service_db;

CREATE TABLE IF NOT EXISTS users (
  user_id  INT AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(100) NOT NULL,
  email    VARCHAR(100) NOT NULL UNIQUE,
  phone    VARCHAR(15),
  password VARCHAR(255) NOT NULL,
  role     ENUM('customer','admin') NOT NULL DEFAULT 'customer'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id     INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT NOT NULL,
  vehicle_number VARCHAR(20) NOT NULL UNIQUE,
  brand          VARCHAR(50) NOT NULL,
  model          VARCHAR(50) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS services (
  service_id   INT AUTO_INCREMENT PRIMARY KEY,
  service_name VARCHAR(100) NOT NULL UNIQUE,
  charge       DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bookings (
  booking_id   INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id   INT NOT NULL,
  service_id   INT NOT NULL,
  service_date DATE NOT NULL,
  status       ENUM('Booked','In Progress','Completed','Delivered') NOT NULL DEFAULT 'Booked',
  remarks      TEXT,
  FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
  FOREIGN KEY (service_id) REFERENCES services(service_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS spare_parts (
  part_id        INT AUTO_INCREMENT PRIMARY KEY,
  part_name      VARCHAR(100) NOT NULL UNIQUE,
  price          DECIMAL(10,2) NOT NULL,
  stock_quantity INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS booking_parts (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  booking_id INT NOT NULL,
  part_id    INT NOT NULL,
  quantity   INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
  FOREIGN KEY (part_id)    REFERENCES spare_parts(part_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bills (
  bill_id        INT AUTO_INCREMENT PRIMARY KEY,
  booking_id     INT NOT NULL UNIQUE,
  service_charge DECIMAL(10,2) NOT NULL,
  parts_total    DECIMAL(10,2) NOT NULL,
  total_amount   DECIMAL(10,2) NOT NULL,
  bill_date      DATE NOT NULL,
  FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE
) ENGINE=InnoDB;
