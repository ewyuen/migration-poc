"""Fixture Generator: Generates C# TestFixtures and Fakes for service dependencies"""
import os
import re
from typing import Dict, List, Tuple, Any, Optional
from agents.test_writer.service_introspector_csharp import ServiceIntrospectorCSharp


class FixtureGenerator:
    """Generates C# TestFixture classes with DI and Mock/Fake implementations"""

    def __init__(self, introspector: ServiceIntrospectorCSharp):
        self.introspector = introspector

    def generate_fixture(self, service_class: str, namespace: str) -> str:
        """
        Generates a TestFixture class for the given service_class, including Fakes for interfaces.
        """
        constructor = self.introspector.find_constructor(service_class)
        
        # Build fields, setup code, and fake classes
        fields = []
        instantiation_args = []
        fake_classes = []
        setup_lines = []
        generated_fakes_set = set()
        
        for param in constructor:
            p_name = param["name"]
            p_type = param["type"]
            
            # 1. Handle IOptions<TOptions>
            if p_type.startswith("IOptions<") and p_type.endswith(">"):
                options_type = p_type[9:-1]
                fields.append(f"        private readonly {p_type} _options;")
                setup_lines.append(f"            _options = Microsoft.Extensions.Options.Options.Create(new {options_type}());")
                instantiation_args.append("_options")
                
            # 2. Handle IValidator<TRequest>
            elif p_type.startswith("IValidator<") and p_type.endswith(">"):
                request_type = p_type[11:-1]
                # Find matching validator class name e.g. AuthRequestValidator
                validator_class = f"{request_type}Validator"
                # If TRequest is AuthRequest, constructor is new AuthRequestValidator()
                fields.append(f"        private readonly {p_type} _{p_name};")
                setup_lines.append(f"            _{p_name} = new {validator_class}();")
                instantiation_args.append(f"_{p_name}")
                
            # 2.5 Handle ILogger<T>
            elif p_type.startswith("ILogger<") and p_type.endswith(">"):
                inner_match = re.search(r'<(.+)>', p_type)
                inner_type = inner_match.group(1) if inner_match else "object"
                fields.append(f"        public FakeLogger<{inner_type}> Logger {{ get; }} = new FakeLogger<{inner_type}>();")
                instantiation_args.append("Logger")
                
                if "FakeLogger" not in generated_fakes_set:
                    fake_classes.append("""    public class FakeLogger<T> : Microsoft.Extensions.Logging.ILogger<T>
    {
        public IDisposable BeginScope<TState>(TState state) => null;
        public bool IsEnabled(Microsoft.Extensions.Logging.LogLevel logLevel) => true;
        public void Log<TState>(Microsoft.Extensions.Logging.LogLevel logLevel, Microsoft.Extensions.Logging.EventId eventId, TState state, Exception exception, Func<TState, Exception, string> formatter) {}
    }""")
                    generated_fakes_set.add("FakeLogger")

            # 2.75 Handle IConfiguration: a real framework interface whose members are never
            # present in Stage-4-introspected source, so it must be wired to a real instance
            # rather than faked (a generated fake would always be an empty, non-compiling stub).
            elif p_type == "IConfiguration":
                fields.append("        private readonly Microsoft.Extensions.Configuration.IConfiguration _configuration;")
                setup_lines.append(
                    "            _configuration = new Microsoft.Extensions.Configuration.ConfigurationBuilder().Build();"
                )
                instantiation_args.append("_configuration")

            # 3. Handle Interface dependencies e.g. IUserRepository
            elif p_type.startswith("I") and p_type[1].isupper():
                prop_name = p_type[1:]
                if "<" in prop_name:
                    prop_name = prop_name.replace("<", "_").replace(">", "")
                
                fake_class_name = f"Fake{prop_name}"
                fields.append(f"        public {fake_class_name} {prop_name} {{ get; }} = new {fake_class_name}();")
                instantiation_args.append(prop_name)
                
                # Generate Fake class definition
                fake_class_code = self._generate_fake_class(p_type)
                fake_classes.append(fake_class_code)
                
            # 4. Fallback default
            else:
                fields.append(f"        private readonly {p_type} _{p_name};")
                setup_lines.append(f"            _{p_name} = default({p_type});")
                instantiation_args.append(f"_{p_name}")

        # Assemble the fixture class code
        lines = []
        lines.append("    public class TestFixture : IDisposable")
        lines.append("    {")
        
        # Fields/Properties
        for f in fields:
            lines.append(f)
        lines.append("")
        
        # Constructor
        lines.append("        public TestFixture()")
        lines.append("        {")
        for s in setup_lines:
            lines.append(s)
        lines.append("        }")
        lines.append("")

        # CreateSystemUnderTest method
        args_str = ", ".join(instantiation_args)
        lines.append(f"        public {service_class} CreateSystemUnderTest()")
        lines.append("        {")
        lines.append(f"            return new {service_class}({args_str});")
        lines.append("        }")
        lines.append("")

        # Dispose method
        lines.append("        public void Dispose()")
        lines.append("        {")
        lines.append("        }")
        lines.append("    }")
        lines.append("")

        # Append fake classes at the bottom
        for fc in fake_classes:
            lines.append(fc)

        return "\n".join(lines)

    def _generate_fake_class(self, interface_name: str) -> str:
        """
        Dynamically construct a Fake class for a given interface
        """
        fake_class_name = f"Fake{interface_name[1:]}"

        # Build the fake from the interface's real, introspected method signatures
        # (parsed from the actual Stage-4 source by ServiceIntrospectorCSharp).
        methods = self.introspector.interfaces.get(interface_name, {}).get("methods", [])

        lines = []
        lines.append(f"    public class {fake_class_name} : {interface_name}")
        lines.append("    {")
        
        # Backing properties for return values and tracking
        properties = []
        method_impls = []
        
        for m in methods:
            m_name = m["name"]
            ret_type = m["return_type"]
            params = m["parameters"]
            
            params_decl = ", ".join(f"{p['type']} {p['name']}" for p in params)
            
            # Task<T> return type
            if ret_type.startswith("Task<") and ret_type.endswith(">"):
                inner_type = ret_type[5:-1]
                prop_name = f"{m_name}Result"
                properties.append(f"        public {inner_type} {prop_name} {{ get; set; }}")
                method_impls.append(f"        public Task<{inner_type}> {m_name}({params_decl}) => Task.FromResult({prop_name});")
            # Task (void) return type
            elif ret_type == "Task":
                count_prop = f"{m_name}CallCount"
                last_arg_props = [f"public {p['type']} Last{m_name}_{p['name']} {{ get; set; }}" for p in params]
                
                properties.append(f"        public int {count_prop} {{ get; set; }}")
                for lap in last_arg_props:
                    properties.append(f"        {lap}")
                    
                impl_body = [f"{count_prop}++;"]
                for p in params:
                    impl_body.append(f"            Last{m_name}_{p['name']} = {p['name']};")
                impl_body.append("            return Task.CompletedTask;")
                
                impl_str = f"        public Task {m_name}({params_decl})\n        {{\n            " + "\n            ".join(impl_body) + "\n        }"
                method_impls.append(impl_str)
            # Regular synchronous return type
            else:
                prop_name = f"{m_name}Result"
                properties.append(f"        public {ret_type} {prop_name} {{ get; set; }}")
                method_impls.append(f"        public {ret_type} {m_name}({params_decl}) => {prop_name};")

        # Combine properties and methods
        for p in properties:
            lines.append(p)
        lines.append("")
        for mi in method_impls:
            lines.append(mi)
            lines.append("")
            
        lines.append("    }")
        return "\n".join(lines)
