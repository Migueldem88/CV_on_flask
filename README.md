# CV_on_flask
A web-site which contains a list of CVs where you can create and edit CVs

To use the app we should create these 3 (three) tables in MYSQL:
CREATE TABLE general(CV_id INTEGER PRIMARY KEY AUTO_INCREMENT, FirstLastName VARCHAR(60), profession VARCHAR(100), age INTEGER(15), Tel VARCHAR(50), email VARCHAR(60));

CREATE TABLE detailed(det_id INTEGER PRIMARY KEY AUTO_INCREMENT, Education VARCHAR(2000), Experience VARCHAR(2000), Skills VARCHAR(2000), Additional_information VARCHAR(2000), CV_id INTEGER(15), FOREIGN KEY (CV_id) REFERENCES general(CV_id));

CREATE TABLE users(user_id INTEGER PRIMARY KEY AUTO_INCREMENT, username VARCHAR(60) unique,
 FL_name VARCHAR(60), email VARCHAR(100), Admin tinyint(25), password VARCHAR(500) unique);
