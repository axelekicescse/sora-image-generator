"""
Test runner for Sora Image Generator.
Runs all unit tests and validates the implementation.
"""
import unittest
import sys
import os
import logging
from unittest import mock

logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s: %(message)s',
                   handlers=[logging.StreamHandler()])

logger = logging.getLogger("sora_test_runner")

def run_all_tests():
    """Run all unit tests for the Sora Image Generator."""
    logger.info("Starting Sora Image Generator test suite")
    
    import sora_utils
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    test_suite.addTest(test_loader.loadTestsFromTestCase(sora_utils.TestSoraUtils))
    test_suite.addTest(test_loader.loadTestsFromTestCase(sora_utils.TestRetryDecorator))
    test_suite.addTest(test_loader.loadTestsFromTestCase(sora_utils.TestWaitForElement))
    test_suite.addTest(test_loader.loadTestsFromTestCase(sora_utils.TestDownloadImage))
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
