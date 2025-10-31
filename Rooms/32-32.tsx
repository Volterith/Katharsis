<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.11.2" name="32-32" tilewidth="32" tileheight="32" tilecount="80" columns="8">
 <image source="32-32.png" width="256" height="320"/>
 <tile id="8">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="10">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="12">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="14">
  <properties>
   <property name="collectable" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="15">
  <properties>
   <property name="healing" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="23">
  <properties>
   <property name="healing" type="bool" value="true"/>
   <property name="respawn_time" type="float" value="15"/>
  </properties>
 </tile>
 <tile id="24">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="26">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="28">
  <properties>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="30">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="ground" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="40">
  <properties>
   <property name="fall" type="bool" value="true"/>
   <property name="fall_on_stand" type="bool" value="true"/>
   <property name="respawn_time" type="float" value="5"/>
  </properties>
 </tile>
 <tile id="41">
  <properties>
   <property name="fall" type="bool" value="true"/>
   <property name="fall_on_stand" type="bool" value="true"/>
   <property name="respawn_time" type="float" value="5"/>
  </properties>
 </tile>
 <tile id="42">
  <properties>
   <property name="fall" type="bool" value="true"/>
   <property name="fall_on_stand" type="bool" value="true"/>
   <property name="respawn_time" type="float" value="5"/>
  </properties>
 </tile>
 <tile id="44">
  <properties>
   <property name="damage" type="float" value="1"/>
   <property name="fall" type="bool" value="true"/>
   <property name="fall_on_pass_under" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="45">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="damage" type="float" value="1"/>
   <property name="knockback" type="float" value="5"/>
  </properties>
 </tile>
 <tile id="46">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="damage" type="float" value="1"/>
   <property name="knockback" type="float" value="5"/>
  </properties>
 </tile>
 <tile id="47">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="damage" type="float" value="1"/>
   <property name="knockback" type="float" value="5"/>
  </properties>
 </tile>
 <tile id="59">
  <properties>
   <property name="platform" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="60">
  <properties>
   <property name="platform" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="61">
  <properties>
   <property name="collidable" type="bool" value="true"/>
   <property name="platform" type="bool" value="true"/>
  </properties>
 </tile>
 <tile id="62">
  <properties>
   <property name="damage" type="int" value="1"/>
   <property name="enemy" type="bool" value="true"/>
   <property name="health" type="int" value="3"/>
   <property name="type" value="MeleeGhost"/>
  </properties>
 </tile>
 <tile id="63">
  <properties>
   <property name="damage" type="int" value="1"/>
   <property name="enemy" type="bool" value="true"/>
   <property name="health" type="int" value="3"/>
   <property name="type" value="RangedGhost"/>
  </properties>
 </tile>
 <tile id="71">
  <properties>
   <property name="enemy" type="bool" value="true"/>
   <property name="type" value="EtherJumperBoss"/>
  </properties>
 </tile>
 <tile id="72">
  <properties>
   <property name="breakable" type="bool" value="true"/>
   <property name="collidable" type="bool" value="true"/>
  </properties>
 </tile>
</tileset>
