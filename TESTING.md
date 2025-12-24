# Testing Instructions for Episodic Simulation System

## Prerequisites
- ROS2 Jazzy environment (either Docker container or native installation)
- All dependencies installed (see README.md)

## Building the Package

```bash
# From the workspace root
cd /root/workspace  # or your workspace directory
colcon build --packages-select turtlebot_simulation
source install/setup.bash
```

## Testing Scenarios

### 1. Basic Episodic Simulation (Default Settings)
```bash
ros2 launch turtlebot_simulation episodic_simulation.launch.py
```

**Expected Behavior:**
- Gazebo launches with GUI
- TurtleBot and 4 colored blocks appear
- Simulation runs for 10 episodes, 60 seconds each
- Console logs show episode progress
- After 10 episodes, system shuts down automatically
- File `episode_scores.txt` is created with 10 score entries

**Validation:**
```bash
# Check that output file exists and has correct format
cat episode_scores.txt

# Expected format:
# # Episode Scores - Generated at <timestamp>
# # Total episodes: 10
# # Episode duration: 60.0 seconds
# # Format: episode_number,score
# 1,<score_value>
# 2,<score_value>
# ...
# 10,<score_value>
```

### 2. Custom Number of Episodes
```bash
ros2 launch turtlebot_simulation episodic_simulation.launch.py num_episodes:=3
```

**Expected Behavior:**
- Runs for 3 episodes only
- Output file contains 3 score entries

### 3. Custom Episode Duration
```bash
ros2 launch turtlebot_simulation episodic_simulation.launch.py num_episodes:=2 episode_duration:=30.0
```

**Expected Behavior:**
- Runs for 2 episodes
- Each episode lasts 30 seconds
- Total run time ~60 seconds + reset time

### 4. Headless Mode (No GUI)
```bash
ros2 launch turtlebot_simulation episodic_simulation.launch.py num_episodes:=5 gui:=false
```

**Expected Behavior:**
- Gazebo runs without GUI (faster)
- All other functionality works the same
- Useful for automated testing/data collection

### 5. Custom Output File
```bash
ros2 launch turtlebot_simulation episodic_simulation.launch.py output_file:=/tmp/my_scores.csv
```

**Expected Behavior:**
- Scores saved to `/tmp/my_scores.csv`
- Original `episode_scores.txt` is not created

## Verification Steps

### Check that /block_distances topic is publishing
```bash
# In a separate terminal during simulation
ros2 topic list | grep block_distances
ros2 topic echo /block_distances
```

**Expected:** Should see Float64 messages with score values being published at ~30 Hz

### Check that /reset_world service is available
```bash
# Before launching or during simulation
ros2 service list | grep reset
```

**Expected:** Should see `/reset_world` service listed

### Monitor episode manager logs
```bash
# During simulation, watch for:
# - "Starting Episode X/Y" messages
# - "Episode X completed" messages
# - "Final score: <value>" messages
# - "Resetting simulation..." messages
# - "Simulation reset successful" messages
# - "All N episodes completed!" at the end
```

### Verify simulation reset between episodes
**Manual check:** If running with GUI, observe that:
- Blocks return to original positions between episodes
- TurtleBot returns to origin
- Simulation state is reset

## Troubleshooting

### Issue: /reset_world service not found
**Solution:** Ensure Gazebo is fully launched. The episode manager waits up to 30 seconds for the service to become available.

### Issue: No scores in output file
**Solution:** 
- Check that block_observer.py is running: `ros2 node list | grep block_observer`
- Check that /block_distances topic is publishing: `ros2 topic echo /block_distances`

### Issue: Simulation doesn't shutdown after all episodes
**Solution:** Check console for errors. May need to manually Ctrl+C to stop.

### Issue: Episode duration seems incorrect
**Solution:** Verify that use_sim_time is set correctly. The episode_manager uses wall clock time.

## Performance Notes

- Each episode takes approximately `episode_duration + 1-2 seconds` (for reset)
- Without GUI, episodes run faster and use less CPU/memory
- Score values should vary based on block positions in simulation

## Data Analysis

After running episodic simulation, you can analyze the scores:

```bash
# View scores
cat episode_scores.txt

# Calculate statistics (requires awk)
awk -F',' 'NR>4 {sum+=$2; count++} END {print "Average:", sum/count}' episode_scores.txt
awk -F',' 'NR>4 {if(min==""){min=max=$2}; if($2>max){max=$2}; if($2<min){min=$2}} END {print "Min:", min, "Max:", max}' episode_scores.txt
```

## Success Criteria

The episodic simulation system is working correctly if:
1. ✅ Simulation runs for specified number of episodes
2. ✅ Each episode runs for specified duration (±1 second)
3. ✅ Simulation resets between episodes
4. ✅ Scores are captured and stored to file
5. ✅ System shuts down automatically after all episodes
6. ✅ Output file has correct format and number of entries
