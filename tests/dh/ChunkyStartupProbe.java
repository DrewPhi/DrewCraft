import com.seibel.distanthorizons.core.wrapperInterfaces.modAccessor.AbstractChunkyAccessor;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import org.popcraft.chunky.ChunkyProvider;

/** Exercises the actual DH class, without starting Minecraft or using an account. */
public final class ChunkyStartupProbe {
    static class Probe extends AbstractChunkyAccessor {
        volatile boolean ready;
        int attempts;
        public String getModName() { return "chunky"; }
        protected void bindOnGenerationProgressEvent() {
            attempts++;
            // Exercise the pinned production provider, not a hand-written error string.
            if (!ready) ChunkyProvider.get();
        }
    }
    static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        Probe delayed = new Probe();
        delayed.tryRunFirstTimeSetup();
        delayed.tryRunFirstTimeSetup();
        require(delayed.attempts == 2, "Unready setup must be retried");
        delayed.ready = true;
        delayed.tryRunFirstTimeSetup();
        delayed.tryRunFirstTimeSetup();
        require(delayed.attempts == 3, "Successful listener must bind exactly once");

        Probe concurrent = new Probe();
        concurrent.ready = true;
        CountDownLatch start = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 32; i++) {
            Thread thread = new Thread(() -> {
                try { start.await(); } catch (InterruptedException e) { throw new RuntimeException(e); }
                for (int n = 0; n < 50; n++) concurrent.tryRunFirstTimeSetup();
            });
            threads.add(thread);
            thread.start();
        }
        start.countDown();
        for (Thread thread : threads) thread.join();
        require(concurrent.attempts == 1, "Concurrent callbacks duplicated the listener");

        Probe unexpected = new Probe() {
            protected void bindOnGenerationProgressEvent() {
                throw new IllegalStateException("Different API failure");
            }
        };
        try {
            unexpected.tryRunFirstTimeSetup();
            throw new AssertionError("Unrelated errors must not be hidden");
        } catch (IllegalStateException expected) {
            require("Different API failure".equals(expected.getMessage()), "Wrong exception propagated");
        }
        Probe nullMessage = new Probe() {
            protected void bindOnGenerationProgressEvent() {
                throw new IllegalStateException();
            }
        };
        try {
            nullMessage.tryRunFirstTimeSetup();
            throw new AssertionError("Null-message errors must not be hidden");
        } catch (IllegalStateException expected) {
            require(expected.getMessage() == null, "Wrong null-message exception");
        }
        System.out.println("CHUNKY_STARTUP_PROBE_PASS");
    }
}
