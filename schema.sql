-- Students Table
CREATE TABLE IF NOT EXISTS students_rgd (
    std_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(100) NOT NULL,
    std_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin Table
CREATE TABLE IF NOT EXISTS admins (
    adm_id INT AUTO_INCREMENT PRIMARY KEY,
    adm_fname VARCHAR(100) UNIQUE NOT NULL,
    adm_lname VARCHAR(100),
    adm_email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(100),
    adm_password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    tchr_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    teacher_password VARCHAR(100)
);