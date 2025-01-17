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