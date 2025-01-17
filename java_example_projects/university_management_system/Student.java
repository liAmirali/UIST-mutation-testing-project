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