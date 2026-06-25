// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class ProjectWD : ModuleRules
{
	public ProjectWD(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"ProjectWD",
			"ProjectWD/Variant_Platforming",
			"ProjectWD/Variant_Platforming/Animation",
			"ProjectWD/Variant_Combat",
			"ProjectWD/Variant_Combat/AI",
			"ProjectWD/Variant_Combat/Animation",
			"ProjectWD/Variant_Combat/Gameplay",
			"ProjectWD/Variant_Combat/Interfaces",
			"ProjectWD/Variant_Combat/UI",
			"ProjectWD/Variant_SideScrolling",
			"ProjectWD/Variant_SideScrolling/AI",
			"ProjectWD/Variant_SideScrolling/Gameplay",
			"ProjectWD/Variant_SideScrolling/Interfaces",
			"ProjectWD/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
