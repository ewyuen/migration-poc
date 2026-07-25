"""Assertion Builder: Maps Gherkin expectations to C# FluentAssertions"""
import re
from typing import Dict, List, Tuple, Any, Optional


class AssertionBuilder:
    """Generates FluentAssertions C# code from Gherkin Then steps"""

    def build_assertion(self, step_text: str, result_var: str = "result") -> str:
        """
        Translates a Gherkin Then step into C# FluentAssertions code
        
        Args:
            step_text: The Then step text (e.g., "authentication should succeed")
            result_var: The name of the variable containing the action output
            
        Returns:
            C# assertion statement
        """
        step_lower = step_text.lower()
        
        # 1. Success assertions
        if "should succeed" in step_lower or "is successful" in step_lower:
            return f"{result_var}.IsSuccess.Should().BeTrue();"
            
        # 2. Failure assertions
        if "should fail" in step_lower or "is failure" in step_lower:
            # Check if there is an error message expected e.g. should fail with error "Age must be positive"
            err_match = re.search(r'(?:with error|message)\s+["\'“]([^"\'”]+)["\'”]', step_lower)
            if err_match:
                err_msg = err_match.group(1)
                return f"{result_var}.IsSuccess.Should().BeFalse();\n            {result_var}.Error.Should().Contain(\"{err_msg}\");"
            
            # Check if there is an error template variable e.g. should fail with error "<error>"
            err_tmpl_match = re.search(r'(?:with error|message)\s+["\'“]?<([\w-]+)>["\'”]?', step_lower)
            if err_tmpl_match:
                err_var = err_tmpl_match.group(1)
                # Keep quotes or let C# variables handle it?
                # Usually in Theory tests, <error> gets compiled as parameter `error`
                return f"{result_var}.IsSuccess.Should().BeFalse();\n            {result_var}.Error.Should().Contain({err_var});"
                
            return f"{result_var}.IsSuccess.Should().BeFalse();"
            
        # 3. Token presence assertions
        if "token should be returned" in step_lower or "token is returned" in step_lower:
            # result is Result<AuthResponse>, and Value has Token
            return f"{result_var}.Value.Should().NotBeNull();\n            {result_var}.Value.Token.Should().NotBeNullOrEmpty();"

        # 4. Specific discount assertions e.g. the discount should be $<discount>
        discount_match = re.search(r'discount\s+(?:should|must)\s+be\s+\$?(\d+(?:\.\d+)?|\b\w+\b|<[\w-]+>)', step_lower)
        if discount_match:
            discount_val = discount_match.group(1)
            # If it's a template variable, strip brackets and convert to appropriate parameter reference
            if discount_val.startswith('<') and discount_val.endswith('>'):
                discount_val = discount_val[1:-1]
                # In C#, if it's passed as a string or decimal. Let's assume the parameter name is 'discount'
                return f"{result_var}.Value.DiscountAmount.Should().Be(decimal.Parse({discount_val}));"
            elif re.match(r'^\d+(\.\d+)?$', discount_val):
                return f"{result_var}.Value.DiscountAmount.Should().Be({discount_val}m);"
            else:
                return f"{result_var}.Value.DiscountAmount.Should().Be({discount_val});"

        # 5. Final amount assertions e.g. the final amount should be $<final>
        final_match = re.search(r'final(?:\s+amount)?\s+(?:should|must)\s+be\s+\$?(\d+(?:\.\d+)?|\b\w+\b|<[\w-]+>)', step_lower)
        if final_match:
            final_val = final_match.group(1)
            if final_val.startswith('<') and final_val.endswith('>'):
                final_val = final_val[1:-1]
                return f"{result_var}.Value.FinalAmount.Should().Be(decimal.Parse({final_val}));"
            elif re.match(r'^\d+(\.\d+)?$', final_val):
                return f"{result_var}.Value.FinalAmount.Should().Be({final_val}m);"
            else:
                return f"{result_var}.Value.FinalAmount.Should().Be({final_val});"

        # 5.5 Repository action assertions (e.g. failed attempt counter should be reset)
        if "failed attempt" in step_lower and "reset" in step_lower:
            return "_fixture.UserRepository.ResetFailedAttemptsAsyncCallCount.Should().Be(1);"
        if "failed attempt" in step_lower and "recorded" in step_lower:
            return "_fixture.UserRepository.RecordFailedAttemptAsyncCallCount.Should().Be(1);"
        if "lockout status" in step_lower and "recorded" in step_lower:
            return "_fixture.UserRepository.RecordFailedAttemptAsyncCallCount.Should().Be(1);"
        if "locked for 15 minutes" in step_lower:
            return "_fixture.UserRepository.RecordFailedAttemptAsyncCallCount.Should().Be(1);"

        # 6. Fallback or generic assertions: e.g. validation should fail
        # Try to parse properties or variables
        # Look for e.g. "<audit-action> should be recorded"
        if "should be recorded" in step_lower or "should be logged" in step_lower:
            return f"// TODO: Verify audit trail contains action matching: {step_text}"

        # If it's a property check e.g. "result should not be null"
        if "not be null" in step_lower:
            return f"{result_var}.Should().NotBeNull();"

        return f"// TODO: Assert: {step_text}"
