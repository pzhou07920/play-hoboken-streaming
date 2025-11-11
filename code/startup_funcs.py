import os
import logger
import pandas as pd
import google_auth as ga

def startup_db_setup():
    # check if broadcast_db.csv exists, if not create it and add header
    if os.path.exists('db/broadcast_db.csv'):
        logger.log("db/broadcast_db.csv exists!")
    else:
        with open('db/broadcast_db.csv', 'x', newline='') as csvfile:
            writer = pd.DataFrame(columns=['stream_name', 'pid', 'broadcast_id'])
            writer.to_csv(csvfile, index=False)

    broadcast_df = pd.read_csv('db/broadcast_db.csv')
    for index, row in broadcast_df.iterrows():
        broadcast_id = row['broadcast_id']
        if ga.get_broadcast_status(broadcast_id) != 'live':
            logger.log(f'Broadcast ID: {broadcast_id} is not live. Removing from db/broadcast_db.csv')
            broadcast_df = broadcast_df[broadcast_df['broadcast_id'] != broadcast_id]
        else:
            # kill the ffmpeg process
            pid = row['pid']
            if pid != '':
                try:
                    logger.log(f'Killing ffmpeg process with PID: {pid}')
                    os.kill(pid, 9)
                except Exception as e:
                    logger.log(f'Error killing ffmpeg process with PID: {pid} | Error: {e}')
            # terminate the broadcast
            ga.terminate_broadcast(broadcast_id)
    broadcast_df.to_csv('db/broadcast_db.csv', index=False)

def startup_wf_setup():
    # Create fresh workflow_db.csv since Queue is empty on startup
    if os.path.exists('db/workflow_db.csv'):
        os.remove('db/workflow_db.csv')
    with open('db/workflow_db.csv', 'x', newline='') as csvfile:
        writer = pd.DataFrame(columns=['stream_name', 'is_running?'])
        writer.to_csv(csvfile, index=False)