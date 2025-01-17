import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class ProfessorTest {
    private Professor professor;

    @BeforeEach
    void setUp() {
        professor = new Professor("Test Professor", 45, "P999", "Computer Science");
    }

    @Test
    public void testProfessorCreation() {
        assertEquals("Test Professor", professor.getName());
        assertEquals("P999", professor.getId());
        assertEquals("Computer Science", professor.getDepartment());
        assertEquals("Professor", professor.getRole());
        assertFalse(professor.isTenured());
    }

    @Test
    public void testAssignCourses() {
        assertTrue(professor.assignCourse("CS101"));
        assertTrue(professor.assignCourse("CS102"));
        assertTrue(professor.assignCourse("CS103"));
        assertFalse(professor.assignCourse("CS104")); // Should fail as max is 3
    }

    @Test
    public void testGrantTenure() {
        assertFalse(professor.isTenured());
        professor.grantTenure();
        assertTrue(professor.isTenured());
    }
}