"""Gherkin Code Mapper: Maps Gherkin steps to C# code blocks using service introspection"""
import re
from typing import Dict, List, Tuple, Any, Optional
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp


class GherkinCodeMapper:
    """Maps Gherkin steps to executable C# Arrange, Act, and Assert statements"""

    def __init__(self, introspector: ServiceIntrospectorCSharp):
        self.introspector = introspector

    def map_arrange_step(self, step_text: str, is_theory: bool, method_params: List[str]) -> List[str]:
        """
        Maps a Given step to C# Arrange code
        """
        code = []
        step_lower = step_text.lower()

        # Clean Gherkin step text from potential markdown/special chars
        step_cleaned = step_text.strip()

        # Helper to decide if we need to declare a variable (not needed if it's a theory parameter)
        def should_declare(var_name: str) -> bool:
            return not is_theory or var_name not in method_params

        matched = False

        # 1. Registered user setup
        user_match = re.search(r'registered\s+user\s+with\s+email\s+["\'“]([^"\'”]+)["\'”]\s+and\s+password\s+["\'“]([^"\'”]+)["\'”]|registered\s+medical\s+user\s+with\s+email\s+["\'“]([^"\'”]+)["\'”]', step_cleaned, re.IGNORECASE)
        if user_match:
            matched = True
            email = user_match.group(1) or user_match.group(3)
            password = user_match.group(2) if len(user_match.groups()) > 1 else None
            if email and should_declare("email"):
                code.append(f'var email = "{email}";')
            if password and should_declare("password"):
                code.append(f'var password = "{password}";')
            code.append('_fixture.UserRepository.ValidateUserResult = true;')

        # 2. Basic user setup (just email)
        user_email_match = re.search(r'user\s+with\s+email\s+["\'“]([^"\'”]+)["\'”]|email\s+address\s+["\'“]([^"\'”]+)["\'”]|medical\s+user\s+["\'“]([^"\'”]+)["\'”]|email\s+["\'“]([^"\'”]+)["\'”]', step_cleaned, re.IGNORECASE)
        if user_email_match:
            matched = True
            email = user_email_match.group(1) or user_email_match.group(2) or user_email_match.group(3) or user_email_match.group(4)
            if should_declare("email"):
                code.append(f'var email = "{email}";')

        # 2.5 Password setup
        password_match = re.search(r'password\s+["\'“]([^"\'”]+)["\'”]', step_cleaned, re.IGNORECASE)
        if password_match:
            matched = True
            password = password_match.group(1)
            if should_declare("password"):
                code.append(f'var password = "{password}";')

        # 3. Account lockout status
        if "account is not locked out" in step_lower:
            matched = True
            code.append('_fixture.UserRepository.IsLockedOutResult = false;')
        elif "account is locked out" in step_lower:
            matched = True
            code.append('_fixture.UserRepository.IsLockedOutResult = true;')

        # 4. Failed login attempts count
        failed_attempts_match = re.search(r'failed\s+login\s+attempts\s+count\s+is\s+(\d+)|has\s+(\d+)\s+failed\s+login\s+attempts', step_cleaned, re.IGNORECASE)
        if failed_attempts_match:
            matched = True
            count = failed_attempts_match.group(1) or failed_attempts_match.group(2)
            code.append(f'_fixture.UserRepository.FailedAttemptsCount = {count};')

        # 5. Patient age
        age_match = re.search(r'patient\s+aged\s+(\d+)\s+years|patient\s+aged\s+(\d+)|patient\s+age\s+of\s+(\d+)|patient\s+age\s+(\d+)', step_cleaned, re.IGNORECASE)
        if age_match:
            matched = True
            age = age_match.group(1) or age_match.group(2) or age_match.group(3) or age_match.group(4)
            if should_declare("age"):
                code.append(f'var age = {age};')
        
        # 6. Medication / treatment cost (also matches general currency value anywhere in the step)
        cost_match = re.search(r'cost\s+of\s+\$?(\d+(?:\.\d+)?)|bill\s+of\s+\$?(\d+(?:\.\d+)?)|with\s+a\s+\$?(\d+(?:\.\d+)?)\s+medical\s+bill|\$(\d+(?:\.\d+)?)', step_cleaned, re.IGNORECASE)
        if cost_match:
            matched = True
            amount = cost_match.group(1) or cost_match.group(2) or cost_match.group(3) or cost_match.group(4)
            if should_declare("amount"):
                code.append(f'var amount = {amount}m;')

        # 7. Valid session token setup
        token_match = re.search(r'valid\s+session\s+token\s+for\s+["\'“]([^"\'”]+)["\'”]', step_cleaned, re.IGNORECASE)
        if token_match:
            matched = True
            email = token_match.group(1)
            if should_declare("token"):
                code.append(f'var email = "{email}";')
                code.append('var token = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes($"{email}:{DateTime.UtcNow.Ticks}"));')
            code.append('_fixture.UserRepository.UserExistsResult = true;')

        # 8. Malformed token setup
        malformed_token_match = re.search(r'expired/malformed\s+token\s+["\'“]([^"\'”]+)["\'”]', step_cleaned, re.IGNORECASE)
        if malformed_token_match:
            matched = True
            token_val = malformed_token_match.group(1)
            if should_declare("token"):
                code.append(f'var token = "{token_val}";')

        # 9. Empty session token
        if "empty session token" in step_lower:
            matched = True
            if should_declare("token"):
                code.append('var token = "";')

        # Default fallback
        if not matched:
            code.append(f'// Given: {step_cleaned}')
        
        return code

    def map_act_step(self, step_text: str, is_theory: bool, method_params: List[str]) -> List[str]:
        """
        Maps a When step to C# Act code
        """
        code = []
        step_lower = step_text.lower()
        step_cleaned = step_text.strip()

        # 1. Authenticate operation
        if "authenticate" in step_lower or "log in" in step_lower:
            # Check if theory parameters are used in step
            email_var = "email"
            password_var = "password"
            
            # If scenario outline uses <email> / <password> in step description
            if "<email>" in step_cleaned or "<password>" in step_cleaned:
                email_var = "email"
                password_var = "password"
            
            # If it's a theory and parameters are named differently, map them
            # Let's check constructor of AuthRequest
            # AuthenticationService.AuthenticateUserAsync(AuthRequest request)
            # Find class AuthRequest in records
            auth_req_record = self.introspector.records.get("AuthRequest")
            if auth_req_record:
                # AuthRequest constructor parameters: usually Email, Password
                # C# DTO: new AuthRequest(email, password)
                code.append(f'var request = new AuthRequest({email_var}, {password_var});')
            else:
                code.append(f'var request = new AuthRequest({email_var}, {password_var});')
                
            code.append('var result = await systemUnderTest.AuthenticateUserAsync(request);')
            return code

        # 2. Calculate discount operation
        if "calculate" in step_lower and "discount" in step_lower:
            age_var = "age"
            amount_var = "amount"
            
            # If it's a theory, parameters from scenario outline table are passed to the method signature.
            # However, the NUnit Theory parameters might be string. We need to parse them if necessary.
            # In C#, NUnit inline data passes them: public void AgeBasedDiscountCalculation(string age, string amount...)
            # So if age and amount are strings, we must parse them.
            age_ref = "int.Parse(age)" if "age" in method_params else "age"
            amount_ref = "decimal.Parse(amount)" if "amount" in method_params else "amount"

            code.append(f'var request = new DiscountRequest({age_ref}, {amount_ref});')
            code.append('var result = await systemUnderTest.CalculateDiscountAsync(request);')
            return code

        # 3. Validate token operation
        if "validate" in step_lower and ("token" in step_lower or "it" in step_lower):
            token_var = "token"
            code.append(f'var result = await systemUnderTest.ValidateSessionTokenAsync({token_var});')
            return code

        # Default fallback
        code.append(f'// When: {step_cleaned}')
        code.append('var result = await Task.FromResult<object>(null);')
        return code

    def map_assert_step(self, step_text: str, is_theory: bool, method_params: List[str], target_method: str = "") -> List[str]:
        """
        Maps a Then step to C# Assert code
        """
        from agents.test_writer.assertion_builder import AssertionBuilder
        builder = AssertionBuilder()
        
        # Decide if return type is bool or Result DTO
        # Determine based on target_method
        return_type = "object"
        if target_method:
            sig = self.introspector.get_method_signature("AuthenticationService", target_method)
            if sig:
                return_type = sig.get("return_type", "object")

        step_cleaned = step_text.strip()
        step_lower = step_cleaned.lower()

        # Handle boolean return type vs Result DTO return type
        if "bool" in return_type.lower() or target_method == "ValidateSessionTokenAsync":
            if "fail" in step_lower or "false" in step_lower:
                return ["result.Should().BeFalse();"]
            elif "succeed" in step_lower or "true" in step_lower:
                return ["result.Should().BeTrue();"]

        # Otherwise use standard AssertionBuilder
        assertion = builder.build_assertion(step_cleaned, "result")
        return assertion.split('\n')
