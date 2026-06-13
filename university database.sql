create table Departments(
	Department_ID INT primary key auto_increment,
    Department_Name Varchar(200) unique
);

create table Books(
	Book_ID int primary key auto_increment,
    Title varchar(285),
    Author varchar(285),
    Total_Copies int,
    Available_Copies int
);


create table Programs(
	Program_ID int primary key auto_increment,
    Department_ID int,
    Program_Name varchar(285),
    Program_Code Varchar(20),
    Total_Seats INT,
    foreign key (Department_ID) references Departments (Department_ID)
    
);

create table Rooms(
	Room_ID int primary key,
    Department_ID int,
    Capacity INT,
    Room_Type enum('Theory', 'Lab'),
    foreign key (Department_ID) references Departments (Department_ID)
);

create table Faculty(
	Faculty_ID int primary key auto_increment,
    First_Name Varchar(100) not null,
    Last_Name Varchar(255) not null,
    Role Varchar(50),
    Department_ID Int,
    Email Varchar(30) Unique not null,
    Phone_no Varchar(30) unique not null,
    foreign key (Department_ID) references Departments (Department_ID)
);

create table Applicants(
	Applicant_ID int primary key auto_increment,
    First_Name Varchar(100) not null,
    Last_Name Varchar(255) not null,
    Email Varchar(30) Unique not null,
    Phone_no Varchar(20) unique not null,
    Address varchar(285),
    City varchar(100),
    Board_Name varchar(100),
    Matric_Marks Decimal(6,2) not null,
    Inter_Marks Decimal(6,2) not null,
    Applied_Program_ID int not null,
    Merit_Score Decimal(5,2),
    Status ENUM ('Pending', 'Merit_List', 'Rejected', 'Enrolled')
    );
alter table applicants 
add District varchar(100)
after phone_no;
    
create table Courses(
	Course_ID int primary key auto_increment,
    Course_Code varchar(10), -- Ex: Cs-102 
    Program_ID int,
    Course_Name Varchar(70) not null unique,
    Credit_Hours INT not null,
    Course_Type enum('Theory', 'Lab'),
    foreign key (Program_ID) references Programs (Program_ID)
    
);


create table Sections(
	Section_ID Int primary key auto_increment,
    Program_ID int,
    Semester_Number int,
    Section_Name Char(1)
);

create table Enrolled_Students(
	Student_ID int primary key auto_increment,
    Applicant_ID int,
    Roll_no Varchar(10),
    Department_ID int,
    Program_ID int,
    Current_Semester smallint,
    foreign key (Applicant_ID) references Applicants (Applicant_ID),
    foreign key (Department_ID) references Departments (Department_ID),
    foreign key (Program_ID) references Programs (Program_ID)
    
);


create table Timetable_Slots(
	Slot_ID int primary key auto_increment,
    Section_ID int,
    Course_ID int,
    Faculty_ID int,
    Room_ID int,
    Day_Of_Week  ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
    Start_Time time,
    End_Time time,
    foreign key (Section_ID) references Sections (Section_ID),
    foreign key (Course_ID) references Courses (Course_ID),
    foreign key (Faculty_ID) references Faculty (Faculty_ID),
    foreign key (Room_ID) references Rooms (Room_ID)
    
);

create table Book_Checkouts(
	Checkout_ID int primary key auto_increment,
    Book_ID int,
    Student_ID int,
    Checkout_Date date,
    Due_Date date,
    Return_Date date,
    foreign key (Book_ID) references Books(Book_ID),
    foreign key (Student_ID) references enrolled_students(Student_ID)
);

create table Financial_Aid(
	Aid_ID int primary key auto_increment,
    Student_ID int,
    Aid_Name varchar(285),
    Discount_Percentage decimal(5,2) ,
    Valid_Until_Semester smallint,
    foreign key (Student_ID) references enrolled_students (Student_ID) 
);

create table Fee_Challans(
	Challan_ID int primary key auto_increment,
    Student_ID int,
    Base_Tuition Decimal(10,2),
    Library_Fine Decimal(7,2),
    Net_Payable Decimal(10,2),
    Due_date date,
    Payment_Status ENUM('Paid', 'Unpaid', 'Partially Paid'),
    foreign key (Student_ID) references enrolled_students (Student_ID) 
);

CREATE TABLE System_Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(100) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('Admin', 'Faculty', 'Student') NOT NULL,
    Reference_ID INT NULL
);

alter table enrolled_students
modify column Roll_no Varchar(20);

CREATE TABLE Student_Grades (
    Grade_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID INT NOT NULL,
    Course_ID INT NOT NULL,
    Semester_Number INT NOT NULL,
    Marks_Obtained DECIMAL(5,2) NOT NULL,
    GPA_Points DECIMAL(3,2) NOT NULL,
    Grade_Letter VARCHAR(2) NOT NULL,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_grades_student FOREIGN KEY (Student_ID) REFERENCES Enrolled_Students(Student_ID) ON DELETE CASCADE,
    CONSTRAINT fk_grades_course FOREIGN KEY (Course_ID) REFERENCES Courses(Course_ID) ON DELETE CASCADE,
    
    -- Pro-Tip Unique Index
    CONSTRAINT unique_student_course UNIQUE (Student_ID, Course_ID)
);


-- 1. Create Departments
INSERT INTO departments (Department_Name) VALUES 
('Computer Science and IT'),
('Management Sciences');

-- 2. Create Programs (Linked to Departments)
INSERT INTO programs (Department_ID, Program_Name, Program_Code, Total_Seats) VALUES 
(1, 'Bachelor of Science in Information Technology (BSIT)', 'BSIT', 50),
(1, 'Bachelor of Science in Computer Science (BSCS)', 'BSCS', 50),
(2, 'Bachelor of Business Administration (BBA)', 'BBA', 50);

-- 3. Create Courses (Linked to Programs)
INSERT INTO courses (Course_Code, Program_ID, Course_Name, Credit_Hours, Course_Type) VALUES 
('IT-101', 1, 'Introduction to Computing', 3, 'Lab'),
('CS-201', 2, 'Data Structures', 3, 'Lab'),
('MGT-301', 3, 'Principles of Management', 3, 'Theory');

-- 4. Create a Test Faculty Member
INSERT INTO faculty (First_Name, Last_Name, Role, Department_ID, Email, Phone_no) VALUES 
('Ahmed', 'Ali', 'Assistant Professor', 1, 'ahmed.ali@mnsuam.edu.pk', '03001234567');

-- 5. Give that Faculty Member a System Login!
INSERT INTO system_users (Username, Password_Hash, Role, Reference_ID) VALUES 
('ahmed.ali@mnsuam.edu.pk', 'faculty123', 'Faculty', 1);


ALTER TABLE student_grades
DROP COLUMN Marks_Obtained,
ADD COLUMN Sessional_Marks DECIMAL(5,2) DEFAULT 0.00 AFTER Semester_Number,
ADD COLUMN Mid_Marks DECIMAL(5,2) DEFAULT 0.00 AFTER Sessional_Marks,
ADD COLUMN Final_Marks DECIMAL(5,2) DEFAULT 0.00 AFTER Mid_Marks,
ADD COLUMN Practical_Marks DECIMAL(5,2) DEFAULT 0.00 AFTER Final_Marks,
ADD COLUMN Total_Obtained DECIMAL(5,2) DEFAULT 0.00 AFTER Practical_Marks,
ADD COLUMN Total_Max DECIMAL(5,2) DEFAULT 100.00 AFTER Total_Obtained;


INSERT INTO timetable_slots ( Section_ID, Course_ID, Faculty_ID, Room_ID, Day_Of_Week, Start_Time, End_Time) 
VALUES ( 1, 1, 1, 101, 'Monday', '09:00:00', '10:30:00');

insert into rooms
values (101 ,1, 50, 'Lab');-- 1. Independent Tables
CREATE TABLE Departments(
    Department_ID INT PRIMARY KEY AUTO_INCREMENT,
    Department_Name VARCHAR(200) UNIQUE
);

CREATE TABLE Books(
    Book_ID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(285),
    Author VARCHAR(285),
    Total_Copies INT,
    Available_Copies INT
);

CREATE TABLE System_Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(100) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('Admin', 'Faculty', 'Student') NOT NULL,
    Reference_ID INT NULL
);

-- 2. Dependent Tables
CREATE TABLE Programs(
    Program_ID INT PRIMARY KEY AUTO_INCREMENT,
    Department_ID INT,
    Program_Name VARCHAR(285),
    Program_Code VARCHAR(20),
    Total_Seats INT,
    FOREIGN KEY (Department_ID) REFERENCES Departments (Department_ID)
);

CREATE TABLE Rooms(
    Room_ID INT PRIMARY KEY,
    Department_ID INT,
    Capacity INT,
    Room_Type ENUM('Theory', 'Lab'),
    FOREIGN KEY (Department_ID) REFERENCES Departments (Department_ID)
);

CREATE TABLE Faculty(
    Faculty_ID INT PRIMARY KEY AUTO_INCREMENT,
    First_Name VARCHAR(100) NOT NULL,
    Last_Name VARCHAR(255) NOT NULL,
    Role VARCHAR(50),
    Department_ID INT,
    Email VARCHAR(50) UNIQUE NOT NULL,
    Phone_no VARCHAR(30) UNIQUE NOT NULL,
    FOREIGN KEY (Department_ID) REFERENCES Departments (Department_ID)
);

CREATE TABLE Applicants(
    Applicant_ID INT PRIMARY KEY AUTO_INCREMENT,
    First_Name VARCHAR(100) NOT NULL,
    Last_Name VARCHAR(255) NOT NULL,
    Email VARCHAR(50) UNIQUE NOT NULL,
    Phone_no VARCHAR(20) UNIQUE NOT NULL,
    Address VARCHAR(285),
    City VARCHAR(100),
    District VARCHAR(100),
    Board_Name VARCHAR(100),
    Matric_Obtained DECIMAL(6,2) NOT NULL,
    Matric_Total DECIMAL(6,2) NOT NULL,
    Inter_Obtained DECIMAL(6,2) NOT NULL,
    Inter_Total DECIMAL(6,2) NOT NULL,
    Applied_Program_ID INT NOT NULL,
    Merit_Score DECIMAL(5,2),
    Status ENUM ('Pending', 'Merit_List', 'Rejected', 'Enrolled') DEFAULT 'Pending'
);

CREATE TABLE Courses(
    Course_ID INT PRIMARY KEY AUTO_INCREMENT,
    Course_Code VARCHAR(10), 
    Program_ID INT,
    Course_Name VARCHAR(70) NOT NULL UNIQUE,
    Credit_Hours INT NOT NULL,
    Course_Type ENUM('Theory', 'Lab'),
    FOREIGN KEY (Program_ID) REFERENCES Programs (Program_ID)
);

CREATE TABLE Sections(
    Section_ID INT PRIMARY KEY AUTO_INCREMENT,
    Program_ID INT,
    Semester_Number INT,
    Section_Name CHAR(1)
);

CREATE TABLE Enrolled_Students(
    Student_ID INT PRIMARY KEY AUTO_INCREMENT,
    Applicant_ID INT,
    Roll_no VARCHAR(20),
    Department_ID INT,
    Program_ID INT,
    Current_Semester SMALLINT,
    Section_ID INT,
    Fee_Status VARCHAR(20) DEFAULT 'Unpaid',
    FOREIGN KEY (Applicant_ID) REFERENCES Applicants (Applicant_ID),
    FOREIGN KEY (Department_ID) REFERENCES Departments (Department_ID),
    FOREIGN KEY (Program_ID) REFERENCES Programs (Program_ID),
    FOREIGN KEY (Section_ID) REFERENCES Sections (Section_ID)
);

CREATE TABLE Timetable_Slots(
    Slot_ID INT PRIMARY KEY AUTO_INCREMENT,
    Section_ID INT,
    Course_ID INT,
    Faculty_ID INT,
    Room_ID INT,
    Day_Of_Week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
    Start_Time TIME,
    End_Time TIME,
    FOREIGN KEY (Section_ID) REFERENCES Sections (Section_ID),
    FOREIGN KEY (Course_ID) REFERENCES Courses (Course_ID),
    FOREIGN KEY (Faculty_ID) REFERENCES Faculty (Faculty_ID),
    FOREIGN KEY (Room_ID) REFERENCES Rooms (Room_ID)
);

CREATE TABLE Book_Checkouts(
    Checkout_ID INT PRIMARY KEY AUTO_INCREMENT,
    Book_ID INT,
    Student_ID INT,
    Checkout_Date DATE,
    Due_Date DATE,
    Return_Date DATE,
    FOREIGN KEY (Book_ID) REFERENCES Books(Book_ID),
    FOREIGN KEY (Student_ID) REFERENCES Enrolled_Students(Student_ID)
);

CREATE TABLE Financial_Aid(
    Aid_ID INT PRIMARY KEY AUTO_INCREMENT,
    Student_ID INT,
    Aid_Name VARCHAR(285),
    Discount_Percentage DECIMAL(5,2),
    Valid_Until_Semester SMALLINT,
    FOREIGN KEY (Student_ID) REFERENCES Enrolled_Students (Student_ID)
);

CREATE TABLE Fee_Challans(
    Challan_ID INT PRIMARY KEY AUTO_INCREMENT,
    Student_ID INT,
    Base_Tuition DECIMAL(10,2),
    Library_Fine DECIMAL(7,2),
    Net_Payable DECIMAL(10,2),
    Due_date DATE,
    Payment_Status ENUM('Paid', 'Unpaid', 'Partially Paid'),
    FOREIGN KEY (Student_ID) REFERENCES Enrolled_Students (Student_ID)
);

CREATE TABLE Student_Grades (
    Grade_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID INT NOT NULL,
    Course_ID INT NOT NULL,
    Semester_Number INT NOT NULL,
    Sessional_Marks DECIMAL(5,2) DEFAULT 0.00,
    Mid_Marks DECIMAL(5,2) DEFAULT 0.00,
    Final_Marks DECIMAL(5,2) DEFAULT 0.00,
    Practical_Marks DECIMAL(5,2) DEFAULT 0.00,
    Total_Obtained DECIMAL(5,2) DEFAULT 0.00,
    Total_Max DECIMAL(5,2) DEFAULT 100.00,
    GPA_Points DECIMAL(3,2) NOT NULL,
    Grade_Letter VARCHAR(2) NOT NULL,
    CONSTRAINT fk_grades_student FOREIGN KEY (Student_ID) REFERENCES Enrolled_Students(Student_ID) ON DELETE CASCADE,
    CONSTRAINT fk_grades_course FOREIGN KEY (Course_ID) REFERENCES Courses(Course_ID) ON DELETE CASCADE,
    CONSTRAINT unique_student_course UNIQUE (Student_ID, Course_ID)
);

-- ==========================================
-- SEED DATA (Aapka Basic Data Jo Insert Hoga)
-- ==========================================

INSERT INTO departments (Department_Name) VALUES 
('Computer Science and IT'),
('Management Sciences');

INSERT INTO programs (Department_ID, Program_Name, Program_Code, Total_Seats) VALUES 
(1, 'Bachelor of Science in Information Technology (BSIT)', 'BSIT', 50),
(1, 'Bachelor of Science in Computer Science (BSCS)', 'BSCS', 50),
(2, 'Bachelor of Business Administration (BBA)', 'BBA', 50);

INSERT INTO courses (Course_Code, Program_ID, Course_Name, Credit_Hours, Course_Type) VALUES 
('IT-101', 1, 'Introduction to Computing', 3, 'Lab'),
('CS-201', 2, 'Data Structures', 3, 'Lab'),
('MGT-301', 3, 'Principles of Management', 3, 'Theory');

INSERT INTO faculty (First_Name, Last_Name, Role, Department_ID, Email, Phone_no) VALUES 
('Ahmed', 'Ali', 'Assistant Professor', 1, 'ahmed.ali@mnsuam.edu.pk', '03001234567');

INSERT INTO system_users (Username, Password_Hash, Role, Reference_ID) VALUES 
('ahmed.ali@mnsuam.edu.pk', 'faculty123', 'Faculty', 1);

INSERT INTO rooms (Room_ID, Department_ID, Capacity, Room_Type) VALUES 
(101, 1, 50, 'Lab');

INSERT INTO sections(Program_ID, Semester_Number, Section_Name) VALUES 
(1, 1, 'A');

INSERT INTO timetable_slots (Section_ID, Course_ID, Faculty_ID, Room_ID, Day_Of_Week, Start_Time, End_Time) VALUES 
(1, 1, 1, 101, 'Monday', '09:00:00', '10:30:00');