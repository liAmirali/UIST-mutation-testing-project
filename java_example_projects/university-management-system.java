// Person.java
public abstract class Person {
    private String name;
    protected int age;
    private String id;

    public Person(String name, int age, String id) {
        this.name = name;
        this.age = age;
        this.id = id;
    }

    public Person(String name, String id) {
        this(name, 0, id);
    }

    public abstract String getRole();

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getId() {
        return id;
    }

    @Override
    public String toString() {
        return "Name: " + name + ", Age: " + age + ", ID: " + id;
    }
}

// Student.java
public class Student extends Person {
    private double gpa;
    private String major;
    private static int studentCount = 0;

    public Student(String name, int age, String id, String major) {
        super(name, age, id);
        this.major = major;
        this.gpa = 0.0;
        studentCount++;
    }

    public Student(String name, String id, String major) {
        super(name, id);
        this.major = major;
        this.gpa = 0.0;
        studentCount++;
    }

    @Override
    public String getRole() {
        return "Student";
    }

    public void updateGpa(double newGpa) {
        if (newGpa >= 0.0 && newGpa <= 4.0) {
            this.gpa = newGpa;
        } else {
            throw new IllegalArgumentException("GPA must be between 0.0 and 4.0");
        }
    }

    public static int getStudentCount() {
        return studentCount;
    }

    public String getMajor() {
        return major;
    }

    public double getGpa() {
        return gpa;
    }
}

// Professor.java
public class Professor extends Person {
    private String department;
    private String[] courses;
    private boolean isTenured;

    public Professor(String name, int age, String id, String department) {
        super(name, age, id);
        this.department = department;
        this.courses = new String[3];
        this.isTenured = false;
    }

    @Override
    public String getRole() {
        return "Professor";
    }

    public boolean assignCourse(String course) {
        for (int i = 0; i < courses.length; i++) {
            if (courses[i] == null) {
                courses[i] = course;
                return true;
            }
        }
        return false;
    }

    public void grantTenure() {
        this.isTenured = true;
    }

    public String getDepartment() {
        return department;
    }

    public boolean isTenured() {
        return isTenured;
    }
}

// Course.java
public class Course {
    private String courseId;
    private String name;
    private Professor instructor;
    private Student[] enrolledStudents;
    private int currentEnrollment;
    private final int MAX_STUDENTS = 30;

    public Course(String courseId, String name, Professor instructor) {
        this.courseId = courseId;
        this.name = name;
        this.instructor = instructor;
        this.enrolledStudents = new Student[MAX_STUDENTS];
        this.currentEnrollment = 0;
        instructor.assignCourse(courseId);
    }

    public boolean enrollStudent(Student student) {
        if (currentEnrollment < MAX_STUDENTS) {
            enrolledStudents[currentEnrollment] = student;
            currentEnrollment++;
            return true;
        }
        return false;
    }

    public void setInstructor(Professor newInstructor) {
        this.instructor = newInstructor;
        newInstructor.assignCourse(courseId);
    }

    public String getCourseId() {
        return courseId;
    }

    public String getName() {
        return name;
    }

    public Professor getInstructor() {
        return instructor;
    }

    public int getCurrentEnrollment() {
        return currentEnrollment;
    }
}

// UniversityDemo.java
public class UniversityDemo {
    public static void main(String[] args) {
        // Create professors
        Professor profJohn = new Professor("John Smith", 45, "P101", "Computer Science");
        Professor profMary = new Professor("Mary Johnson", 50, "P102", "Mathematics");

        // Create students
        Student student1 = new Student("Alice Brown", 20, "S101", "Computer Science");
        Student student2 = new Student("Bob Wilson", "S102", "Mathematics");
        
        // Update student GPA
        student1.updateGpa(3.8);
        student2.updateGpa(3.9);

        // Create courses
        Course javaCourse = new Course("CS101", "Java Programming", profJohn);
        Course mathCourse = new Course("MATH101", "Advanced Calculus", profMary);

        // Enroll students
        javaCourse.enrollStudent(student1);
        mathCourse.enrollStudent(student2);

        // Grant tenure to a professor
        profJohn.grantTenure();

        // Print some information
        System.out.println("Total number of students: " + Student.getStudentCount());
        System.out.println("Professor " + profJohn.getName() + " is" + 
                          (profJohn.isTenured() ? " " : " not ") + "tenured");
        System.out.println("Student " + student1.getName() + " has GPA: " + student1.getGpa());
        System.out.println("Course " + javaCourse.getName() + " has " + 
                          javaCourse.getCurrentEnrollment() + " enrolled students");
    }
}