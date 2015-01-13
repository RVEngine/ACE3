class CfgVehicles {
		class Logic;
		class Module_F: Logic {
			class ArgumentsBaseUnits {
			};
		};
		class GVAR(Module): Module_F {
		scope = 2; 
		displayName = "Basic Ballistics [ACE]";
		icon = "\cse\cse_main\data\cse_rifle_module.paa"; // TODO find a new module icon
		category = "cseModules"; // TODO find a new module category
		function = FUNC(enableModule);
		functionPriority = 1;
		isGlobal = 1;
		isTriggerActivated = 0;
		class Arguments {
			class forAI {
				displayName = "Enable for AI";
				description = "Should the module be enabled for AI";
				typeName = "BOOL";
				defaultValue = 0;
			};
		};
	};
};
