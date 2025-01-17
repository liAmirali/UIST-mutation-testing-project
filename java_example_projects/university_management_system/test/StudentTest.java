import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;

public class StudentTest {
    private Student student;

    @Before
    public void setUp() {
        student = new Student("Test Student", 20, "S999", "Computer Science");
    }

    @Test
    public void testStudentCreation() {
        assertEquals("Test Student", student.getName());
        assertEquals("S999", student.getId());
        assertEquals("Computer Science", student.getMajor());
        assertEquals(0.0, student.getGpa());
        assertEquals("Student", student.getRole());
    }

    @Test
    public void testUpdateValidGpa() {
        student.updateGpa(3.5);
        assertEquals(3.5, student.getGpa());
    }

    @Test
    public void testUpdateInvalidGpa() {
        assertThrows(IllegalArgumentException.class, () -> student.updateGpa(4.5));
        assertThrows(IllegalArgumentException.class, () -> student.updateGpa(-0.5));
    }

    @Test
    public void testStudentCount() {
        int initialCount = Student.getStudentCount();
        new Student("Another Student", "S888", "Mathematics");
        assertEquals(initialCount + 1, Student.getStudentCount());
    }
}