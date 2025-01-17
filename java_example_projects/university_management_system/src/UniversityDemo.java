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