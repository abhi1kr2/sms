CREATE DATABASE IF NOT EXISTS rkdf_pro;
USE rkdf_pro;


-- school_info Tables
CREATE TABLE school_info (
    id INT PRIMARY KEY DEFAULT 1122,
    school_name VARCHAR(150),
    address VARCHAR(255),
    phone VARCHAR(20),
    logo TEXT
);

-- Admin Table
CREATE TABLE IF NOT EXISTS admins (
    adm_id INT AUTO_INCREMENT PRIMARY KEY,
    adm_fname VARCHAR(100) NOT NULL,
    adm_lname VARCHAR(100),
    adm_email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    adm_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;



-- classes Tables
CREATE TABLE classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'Active'
) ENGINE=InnoDB;



-- Students Table
CREATE TABLE IF NOT EXISTS students_rgd (
    std_id INT AUTO_INCREMENT PRIMARY KEY,
    reg_id VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    std_dob DATE,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    class_id INT NOT NULL,
    father_name VARCHAR(100) NOT NULL,
    mother_name VARCHAR(100),
    parent_phone VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    state VARCHAR(100),
    pincode VARCHAR(10),
    prev_school_name VARCHAR(150),
    prev_school_address VARCHAR(255),
    admission_date DATE ,
    std_img TEXT,
    status VARCHAR(20) DEFAULT 'Active',
    std_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_student_class
        FOREIGN KEY (class_id)
        REFERENCES classes(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- SUBJECTS
CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    class_id INT,
    passing_marks INT DEFAULT 33,

    UNIQUE KEY uniq_subject_class (name, class_id),

    CONSTRAINT fk_subject_class
        FOREIGN KEY (class_id)
        REFERENCES classes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- teachers Table
CREATE TABLE IF NOT EXISTS teachers (
    tchr_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    tchr_dob DATE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    class_id INT,  -- ⭐ optional but useful
    teacher_password VARCHAR(255),
    tchr_img TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_teacher_class
        FOREIGN KEY (class_id)
        REFERENCES classes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- EXAMS Tables
CREATE TABLE exams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    class_id INT NOT NULL,
    total_marks INT DEFAULT 100,
    exam_date DATE,
    status VARCHAR(20) DEFAULT 'Active', -- Active / Inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uniq_exam_class (name, class_id),

    CONSTRAINT fk_exam_class
        FOREIGN KEY (class_id)
        REFERENCES classes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- MARKS (core table)
CREATE TABLE IF NOT EXISTS marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    std_id INT NOT NULL,
    subject_id INT NOT NULL,
    exam_id INT NOT NULL,
    marks_obtained INT NOT NULL CHECK (marks_obtained >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_mark (std_id, subject_id, exam_id),

    CONSTRAINT fk_marks_student
        FOREIGN KEY (std_id)
        REFERENCES students_rgd(std_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_marks_subject
        FOREIGN KEY (subject_id)
        REFERENCES subjects(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_marks_exam
        FOREIGN KEY (exam_id)
        REFERENCES exams(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- enquiries Table
CREATE TABLE IF NOT EXISTS enquiries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    course VARCHAR(100) NOT NULL,
    message TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


-- Notices - Table
CREATE TABLE IF NOT EXISTS notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    notice_date DATE,                     -- display date
    expiry_date DATE,                     -- optional
    status VARCHAR(20) DEFAULT 'Active',  -- Active / Expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;



-- Gallery - Table
CREATE TABLE IF NOT EXISTS gallery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    image_path VARCHAR(255) NOT NULL,   -- store file path
    category VARCHAR(100),              -- Event, Sports, Annual Day
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


--Create table as per above order



-- RESET--
-- DROP table marks;
-- DROP table students_rgd;
-- DROP table classes;
-- DROP table subjects;
-- DROP table exams;
-- DROP table school_info;
-- DROP table teachers;


--INSERT SOME DATE--

-- INSERT INTO classes (class_name) VALUES
-- ('Pre-Nursery to Primary'),
-- ('Middle Classes'),
-- ('High Classes'),
-- ('Special Education');




-- INSERT INTO students_rgd 
-- (reg_id, first_name, last_name, email, phone, father_name, parent_phone, class, std_password) VALUES
-- (1001, 'Rahul', 'Kumar', 'rahul@test.com', '7770000001', 'Laxman', '7770000001', '10th', 'student123'),
-- (1002, 'Amit', 'Sharma', 'amit@test.com', '7770000002', 'Murari', '7770000001', '10th', 'student123'),
-- (1003, 'Neha', 'Singh', 'neha@test.com', '7770000003', 'Kunal', '7770000001', '10th', 'student123');



-- DROP ALL TABLES (SAFE ORDER)/:

-- SET FOREIGN_KEY_CHECKS = 0;

-- DROP TABLE IF EXISTS marks;
-- DROP TABLE IF EXISTS exams;
-- DROP TABLE IF EXISTS subjects;
-- DROP TABLE IF EXISTS enquiries;
-- DROP TABLE IF EXISTS teachers;
-- DROP TABLE IF EXISTS admins;
-- DROP TABLE IF EXISTS students_rgd;

-- SET FOREIGN_KEY_CHECKS = 1;