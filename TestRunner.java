import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;

import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class TestRunner {
    static class TestResult {
        String test_name;
        String test_unique_id;
        boolean is_passed;
        String error_message;

        public TestResult(String name, String id, boolean passed, String error) {
            this.test_name = name;
            this.test_unique_id = id;
            this.is_passed = passed;
            this.error_message = error;
        }
    }

    static class TestClassResult {
        String test_class_name;
        int passed_tests;
        int failed_tests;
        int total_tests;
        List<TestResult> test_results;

        public TestClassResult(String className) {
            this.test_class_name = className;
            this.test_results = new ArrayList<>();
            this.passed_tests = 0;
            this.failed_tests = 0;
            this.total_tests = 0;
        }
    }

    static class TestSuiteResult {
        String timestamp;
        List<TestClassResult> test_classes;
        boolean compiled;
        String compile_error;

        public TestSuiteResult(List<TestClassResult> testClasses) {
            this.timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
            this.test_classes = testClasses;
            this.compiled = true;
            this.compile_error = null;
        }
    }

    static class TestExecutionListenerImpl implements TestExecutionListener {
        private final Map<String, TestClassResult> results = new HashMap<>();
        private final Map<String, TestIdentifier> testMethods = new HashMap<>();

        @Override
        public void executionStarted(TestIdentifier testIdentifier) {
            if (testIdentifier.isTest()) {
                testMethods.put(testIdentifier.getUniqueId(), testIdentifier);
            }
        }

        @Override
        public void executionFinished(TestIdentifier testIdentifier, TestExecutionResult testExecutionResult) {
            if (testIdentifier.isTest()) {
                String uniqueId = testIdentifier.getUniqueId();
                String className = extractClassName(uniqueId);
                String methodName = extractMethodName(uniqueId);

                TestClassResult classResult = results.computeIfAbsent(className,
                        k -> new TestClassResult(className));

                boolean isPassed = testExecutionResult.getStatus() == TestExecutionResult.Status.SUCCESSFUL;
                String errorMessage = null;
                if (!isPassed && testExecutionResult.getThrowable().isPresent()) {
                    errorMessage = testExecutionResult.getThrowable().get().getMessage();
                }

                TestResult testResult = new TestResult(
                        methodName,  // Use the extracted method name instead of display name
                        uniqueId,   // Use the full unique ID
                        isPassed,
                        errorMessage
                );

                classResult.test_results.add(testResult);
                if (isPassed) {
                    classResult.passed_tests++;
                } else {
                    classResult.failed_tests++;
                }
                classResult.total_tests++;
            }
        }

        private String extractClassName(String uniqueId) {
            // Extract class name from format: "[engine:junit-jupiter]/[class:CourseTest]/[method:testSetInstructor()]"
            int classStart = uniqueId.indexOf("[class:");
            if (classStart != -1) {
                int classEnd = uniqueId.indexOf("]", classStart);
                if (classEnd != -1) {
                    return uniqueId.substring(classStart + 7, classEnd);
                }
            }
            return "Unknown";
        }

        private String extractMethodName(String uniqueId) {
            // Extract method name from format: "[engine:junit-jupiter]/[class:CourseTest]/[method:testSetInstructor()]"
            int methodStart = uniqueId.indexOf("[method:");
            if (methodStart != -1) {
                int methodEnd = uniqueId.indexOf("]", methodStart);
                if (methodEnd != -1) {
                    String methodWithParens = uniqueId.substring(methodStart + 8, methodEnd);
                    // Remove the parentheses at the end if they exist
                    if (methodWithParens.endsWith("()")) {
                        return methodWithParens.substring(0, methodWithParens.length() - 2);
                    }
                    return methodWithParens;
                }
            }
            return "Unknown";
        }

        public List<TestClassResult> getResults() {
            return new ArrayList<>(results.values());
        }
    }


    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Please provide test class names as arguments");
            System.out.println("Usage: java TestRunner TestClass1 TestClass2 ...");
            return;
        }

        List<Class<?>> testClasses = new ArrayList<>();
        for (String className : args) {
            try {
                className = className.replace(".class", "");
                Class<?> testClass = Class.forName(className);
                testClasses.add(testClass);
            } catch (ClassNotFoundException e) {
                System.err.println("Could not load test class: " + className);
                System.err.println("Error: " + e.getMessage());
            }
        }

        if (testClasses.isEmpty()) {
            System.out.println("No valid test classes provided");
            return;
        }

        runTests(testClasses.toArray(new Class<?>[0]));
    }

    public static void runTests(Class<?>... testClasses) {
        LauncherDiscoveryRequestBuilder requestBuilder = LauncherDiscoveryRequestBuilder.request();
        Arrays.stream(testClasses)
                .forEach(testClass -> requestBuilder.selectors(DiscoverySelectors.selectClass(testClass)));

        LauncherDiscoveryRequest request = requestBuilder.build();
        Launcher launcher = LauncherFactory.create();

        TestExecutionListenerImpl listener = new TestExecutionListenerImpl();
        launcher.registerTestExecutionListeners(listener);

        launcher.execute(request);

        // Create JSON output with timestamp
        TestSuiteResult suiteResult = new TestSuiteResult(listener.getResults());
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(suiteResult);

        String filename = "test_results.json";

        // Write to file
        try (FileWriter writer = new FileWriter(filename)) {
            writer.write(json);
            System.out.println("Test results have been written to " + filename);
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
        }
    }
}