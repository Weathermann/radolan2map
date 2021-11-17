<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" maxScale="0" styleCategories="AllStyleCategories" version="3.6.2-Noosa" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <rasterrenderer opacity="1" classificationMin="200" alphaBand="-1" type="singlebandpseudocolor" classificationMax="4095" band="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Exact</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader clip="0" colorRampType="DISCRETE" classificationMode="1">
          <colorramp name="[source]" type="gradient">
            <prop k="color1" v="255,255,204,255"/>
            <prop k="color2" v="0,104,55,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255"/>
          </colorramp>
          <item label="bis 200" color="#e8810a" value="200" alpha="255"/>
          <item label="bis 250" color="#f7b406" value="250" alpha="255"/>
          <item label="bis 300" color="#f8da02" value="300" alpha="255"/>
          <item label="bis 350" color="#c6ca08" value="350" alpha="255"/>
          <item label="bis 400" color="#8cad0c" value="400" alpha="255"/>
          <item label="bis 450" color="#38880f" value="450" alpha="255"/>
          <item label="bis 500" color="#076819" value="500" alpha="255"/>
          <item label="bis 600" color="#0d827d" value="600" alpha="255"/>
          <item label="bis 700" color="#0372c5" value="700" alpha="255"/>
          <item label="bis 800" color="#1442ad" value="800" alpha="255"/>
          <item label="bis 900" color="#0c147c" value="900" alpha="255"/>
          <item label="bis 1000" color="#000254" value="1000" alpha="255"/>
          <item label="bis 1500" color="#530053" value="1500" alpha="255"/>
          <item label="> 1500" color="#975097" value="4095" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" saturation="0" colorizeBlue="128" grayscaleMode="0" colorizeRed="255" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
