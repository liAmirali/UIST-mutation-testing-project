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