import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;
import org.junit.platform.launcher.listeners.SummaryGeneratingListener;
import org.junit.platform.launcher.listeners.TestExecutionSummary;
import org.junit.platform.engine.discovery.DiscoverySelectors;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class TestRunner {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Please provide test class names as arguments");
            System.out.println("Usage: java TestRunner TestClass1 TestClass2 ...");
            return;
        }

        List<Class<?>> testClasses = new ArrayList<>();
        for (String className : args) {
            try {
                // Remove .class extension if present
                className = className.replace(".class", "");
                // Load the class using the class name
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
        // Build request with all test classes
        LauncherDiscoveryRequestBuilder requestBuilder = LauncherDiscoveryRequestBuilder.request();
        Arrays.stream(testClasses)
              .forEach(testClass -> requestBuilder.selectors(DiscoverySelectors.selectClass(testClass)));

        LauncherDiscoveryRequest request = requestBuilder.build();

        // Create a launcher to run the tests
        Launcher launcher = LauncherFactory.create();

        // Add a listener to capture test execution summary
        SummaryGeneratingListener listener = new SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);

        // Execute the tests
        launcher.execute(request);

        // Get the summary of the test run
        TestExecutionSummary summary = listener.getSummary();

        System.out.println("\nTest Summary:");
        System.out.println("Classes tested: " + Arrays.stream(testClasses)
                                                    .map(Class::getSimpleName)
                                                    .collect(Collectors.joining(", ")));

        summary.getFailures().forEach(failure -> {
            System.out.println("TEST ID:" + failure.getTestIdentifier().getUniqueId());
            System.out.println("EXCEPTION:" + failure.getException());
        });

        System.out.println("Tests Found: " + summary.getTestsFoundCount());
        System.out.println("Tests Succeeded: " + summary.getTestsSucceededCount());
        System.out.println("Tests Failed: " + summary.getTestsFailedCount());
        System.out.println("Tests Skipped: " + summary.getTestsSkippedCount());

        // Print details of failed tests (if any)
        if (summary.getTestsFailedCount() > 0) {
            System.out.println("\nFailed Tests Details:");
            summary.getFailures().forEach(failure -> {
                System.out.println("Failed Test: " + failure.getTestIdentifier().getDisplayName());
                System.out.println("Reason: " + failure.getException().getMessage());
            });
        }
    }
}