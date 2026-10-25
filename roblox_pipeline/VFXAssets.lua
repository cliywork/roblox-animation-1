-- VFXAssets (synced by Rojo into ReplicatedStorage) — the vetted particle textures for the fight.
-- Each entry: the IMAGE id (not the store decal id), its flipbook grid, and how it must be blended.
-- Picked in the VFX lab (ServerStorage.VFXLab holds the source decals): tested as live emitters
-- against the Titan lighting. Explosion sheets have black backgrounds -> LightEmission = 1 (additive).
return {
	smokeSoft = { image = "rbxassetid://13026594575", layout = Enum.ParticleFlipbookLayout.Grid8x8,
		mode = Enum.ParticleFlipbookMode.Loop, additive = false,
		source = "Creator Store 13026594616 'Transparent smoke particle 1' (kirbyzaz)" },
	-- rejected: Creator Store 79643461976843 'Smoke Flipbook' (image 98017427798572) has an opaque
	-- background -> renders as hard squares when not additive.
	fireball = { image = "rbxassetid://15855570024", layout = Enum.ParticleFlipbookLayout.Grid8x8,
		mode = Enum.ParticleFlipbookMode.OneShot, additive = true,
		source = "Creator Store 15855570057 '8X8 Explosion Flipbook' (gameris125454)" },
	fireballAlt = { image = "rbxassetid://13651663811", layout = Enum.ParticleFlipbookLayout.Grid8x8,
		mode = Enum.ParticleFlipbookMode.OneShot, additive = true,
		source = "Creator Store 13651663861 'Explosion Flipbook' 8x8 one-shot (Outlaw_Sinister)" },
}
