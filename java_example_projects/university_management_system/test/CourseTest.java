import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;

public class CourseTest {
    private Course course;
    private Professor professor;
    private Student student;

    @Before
    public void setUp() {
        professor = new Professor("Test Professor", 45, "P999", "Computer Science");
        course = new Course("CS101", "Test Course", professor);
        student = new Student("Test Student", 20, "S999", "Computer Science");
    }

    @Test
    public void testCourseCreation() {
        assertEquals("CS101", course.getCourseId());
        assertEquals("Test Course", course.getName());
        assertEquals(professor, course.getInstructor());
        assertEquals(0, course.getCurrentEnrollment());
    }

    @Test
    public void testEnrollStudent() {
        assertTrue(course.enrollStudent(student));
        assertEquals(1, course.getCurrentEnrollment());
    }

    @Test
    public void testSetInstructor() {
        Professor newProfessor = new Professor("New Professor", 40, "P888", "Computer Science");
        course.setInstructor(newProfessor);
        assertEquals(newProfessor, course.getInstructor());
    }

    @Test
    public void testMaxEnrollment() {
        // Try to enroll 31 students (max is 30)
        for (int i = 0; i < 31; i++) {
            Student student = new Student("Student" + i, 20, "S" + i, "Computer Science");
            if (i < 30) {
                assertTrue(course.enrollStudent(student));
            } else {
                assertFalse(course.enrollStudent(student));
            }
        }
        assertEquals(30, course.getCurrentEnrollment());
    }
}
