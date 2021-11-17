<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" version="3.6.2-Noosa" maxScale="1000" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer classificationMax="500" classificationMin="25" band="1" type="singlebandpseudocolor" opacity="1" alphaBand="-1">
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
        <colorrampshader classificationMode="1" colorRampType="DISCRETE" clip="0">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="255,255,204,255"/>
            <prop k="color2" v="0,104,55,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255"/>
          </colorramp>
          <item alpha="179" color="#e8810a" label="bis 25" value="25"/>
          <item alpha="204" color="#f7b406" label="bis 50" value="50"/>
          <item alpha="230" color="#f8da02" label="bis 75" value="75"/>
          <item alpha="255" color="#c6ca08" label="bis 100" value="100"/>
          <item alpha="255" color="#8cad0c" label="bis 125" value="125"/>
          <item alpha="255" color="#38880f" label="bis 150" value="150"/>
          <item alpha="255" color="#076819" label="bis 175" value="175"/>
          <item alpha="255" color="#0d827d" label="bis 200" value="200"/>
          <item alpha="255" color="#0372c5" label="bis 225" value="225"/>
          <item alpha="255" color="#1442ad" label="bis 250" value="250"/>
          <item alpha="255" color="#0c147c" label="bis 275" value="275"/>
          <item alpha="255" color="#000254" label="bis 300" value="300"/>
          <item alpha="255" color="#530053" label="bis 325" value="325"/>
          <item alpha="255" color="#975097" label="bis 350" value="350"/>
          <item alpha="255" color="#ffbdff" label="> 350" value="500"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeRed="255" colorizeStrength="100" colorizeBlue="128" grayscaleMode="0" colorizeGreen="128" colorizeOn="0" saturation="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
