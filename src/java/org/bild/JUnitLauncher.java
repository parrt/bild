package org.bild;

import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;

public class JUnitLauncher {
	public static void main(String[] args) throws Exception {
		if ( args.length<1 ) {
			return;
		}
		String className = args[0];
		JUnitCore junit = new JUnitCore();
		junit.addListener(
			new RunListener() {
				@Override
				public void testRunFinished(Result result) throws Exception {
					super.testRunFinished(result);
//					System.out.println("finished "+result);
				}
			}
		);
		ByteArrayOutputStream stdout = new ByteArrayOutputStream();
		ByteArrayOutputStream stderr = new ByteArrayOutputStream();
		PrintStream stderr__ = System.err;
		PrintStream stdout__ = System.out;
		System.setOut(new PrintStream(stdout));
		System.setErr(new PrintStream(stderr));
		Result results;
		try {
			results = junit.run(Class.forName(className));
		}
		finally {
			System.setOut(stdout__);
			System.setErr(stderr__);
		}
		System.out.println(className+": "+results.getRunCount()+" tests, "+results.getFailureCount()+" failures");
		if ( results.getFailures()!=null ) {
			for (Failure f:results.getFailures()) {
				String methodName = "\t"+f.getTestHeader().replaceAll("\\(.*?\\)", "()");
				System.out.println(methodName+": "+f.getMessage());
			}
		}
	}
}
