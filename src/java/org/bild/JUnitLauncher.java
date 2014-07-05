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
		boolean verbose = false;
		String className = args[0];
		if ( args[0].equals("-verbose") ) {
			verbose = true;
			if ( args.length<2 ) {
				return;
			}
			className = args[1];
		}
		final ByteArrayOutputStream stdout = new ByteArrayOutputStream();
		final ByteArrayOutputStream stderr = new ByteArrayOutputStream();
		JUnitCore junit = new JUnitCore();
		junit.addListener(
			new RunListener() {
				@Override
				public void testRunFinished(Result result) throws Exception {
					super.testRunFinished(result);
				}
			}
		);
		PrintStream stderr__ = System.err;
		PrintStream stdout__ = System.out;
		PrintStream out = new PrintStream(stdout);
		System.setOut(out);
		PrintStream err = new PrintStream(stderr);
		System.setErr(err);
		Result results;
		try {
			results = junit.run(Class.forName(className));
		}
		finally {
			out.flush();
			err.flush();
			System.setOut(stdout__);
			System.setErr(stderr__);
		}
		if ( verbose ) {
			System.out.println(stdout);
			System.err.println(stderr);
		}
		System.out.println(className+": "+results.getRunCount()+" tests, "+results.getFailureCount()+" failures");
		if ( results.getFailures()!=null ) {
			for (Failure f:results.getFailures()) {
				String methodName = "\t"+f.getTestHeader().replaceAll("\\(.*?\\)", "()");
				System.out.println(methodName+": "+f.getMessage());
				if ( verbose ) {
					System.out.println(f.getTrace());
				}
			}
		}
	}
}
