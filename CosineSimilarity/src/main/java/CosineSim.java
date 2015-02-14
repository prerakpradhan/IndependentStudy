/**
 * Created by nishant on 2/13/15.
 */
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;

public class CosineSim {

    private static Connection con;
    private String filename;
    public CosineSim(String filename){
        this.filename=filename;
        try {
            Class.forName("com.mysql.jdbc.Driver");
            con=DriverManager.getConnection("jdbc:mysql://localhost/dbname","username","password");


        } catch (ClassNotFoundException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            System.exit(-1);
        }
        catch(SQLException e){
            e.printStackTrace();
            System.exit(-1);
        }
    }

    public void closeConnection() throws Exception{
        if(con!=null)
            con.close();
    }

    public void test() throws Exception{
        Map<String,List<String>> maps = getClusterMap();
        System.out.println(maps.size());
        System.out.println(maps.get("1:1:1000").size());
    }

    public Map<String,List<String>> getClusterMap() throws Exception{

        BufferedReader br =new BufferedReader(new FileReader(new File(filename)));
        String line;


        Map<String,List<String>> clusterMap=new HashMap<String,List<String>>();

        while((line=br.readLine()) != null){
            String[] clust_info=line.split("\t");
            String patent=clust_info[0];
            String cluster = clust_info[1].substring(0,clust_info[1].lastIndexOf(':'));
            if(clusterMap.containsKey(cluster))
                clusterMap.get(cluster).add(patent);
            else{
                ArrayList<String> patents=new ArrayList<String>();
                patents.add(patent);
                clusterMap.put(cluster,patents);

            }
        }

        br.close();
        return clusterMap;
    }

    private int[][] buildIncidenceMatrix(ArrayList<String> patents, HashSet<String> bigrams) throws Exception{
        int[][] incidence=new int[patents.size()][bigrams.size()];
        ArrayList<String> bgarray=new ArrayList<String>();
        bgarray.addAll(bigrams);

        int i=0;
        String query="select bigram,count from bigrams where patent_id=?";
        PreparedStatement stmt=con.prepareStatement(query);

        for(String patent: patents){
            //get list of bigrams for that patent and count
            stmt.setString(1, patent);
            ResultSet rset=stmt.executeQuery();
            while(rset.next()){
                int index = bgarray.indexOf(rset.getString("bigram"));
                int count = Integer.parseInt(rset.getString("count"));
                incidence[i][index]=count;
            }
            i++;
            rset.close();
        }
        stmt.close();
        return incidence;
    }

    private double getCosineSimilarity(int[][] incidence){
        //double cosine_similarity=-10;
        if(incidence.length < 2)
            return -10;

        int cols=incidence[0].length;
        int[] rowsum=new int[incidence.length];
        for(int i=0;i<incidence.length;i++){
            int sum=0;
            for(int j=0; j<incidence[i].length;j++)
                sum=(int) (sum+Math.pow(incidence[i][j],2));;
            rowsum[i]=sum;
        }


        double temp=0;
        for(int i=0;i<cols;i++){
            temp=temp+incidence[0][i]*incidence[1][i];
        }

        for(int i=0;i<rowsum.length;i++)
            temp=temp/Math.sqrt(rowsum[i]);

        return temp;

        //return cosine_similarity;
    }


    private ArrayList<String> getBigramsFromPatents(String patentid) throws Exception{
        String query="select bigram from bigrams where patent_id=?";
        PreparedStatement stmt=con.prepareStatement(query);
        stmt.setString(1, patentid);
        ResultSet rset=stmt.executeQuery();
        ArrayList<String> bigrams=new ArrayList<String>();
        while(rset.next())
            bigrams.add(rset.getString("bigram"));
        stmt.close();
        rset.close();
        return bigrams;
    }

    private void writeResults(double cos_sim, String patent1, String patent2,String cluster1,String cluster2) throws Exception {
        File results=new File("results.txt");
        results.createNewFile();
        FileWriter fw=new FileWriter("results.txt",true);
        fw.write(patent1+"\t"+patent2+"\t"+cluster1+"\t"+cluster2+"\t"+cos_sim+"\n");
        fw.close();

    }

    public void calculatePairwiseSimilarity() throws Exception{


        Map<String,List<String>> clusterMaps=getClusterMap();
        Set<String> cluster_set=clusterMaps.keySet();
        String[] clusters=cluster_set.toArray(new String[cluster_set.size()]);

        double cos_sim=-10;

        for(int i=0;i<clusters.length;i++) {

            List<String> patents1=clusterMaps.get(clusters[i]);

            for (int j = i + 1; j < clusters.length; j++) {

                List<String> patents2=clusterMaps.get(clusters[j]);

                for(String p1 : patents1) {
                    ArrayList<String> bigrams1 = getBigramsFromPatents(p1);
                    for (String p2 : patents2) {
                        ArrayList<String> bigrams2=getBigramsFromPatents(p2);
                        HashSet<String> bigramset=new HashSet<String>();
                        bigramset.addAll(bigrams1);
                        bigramset.addAll(bigrams2);

                        ArrayList<String> pat=new ArrayList<String>();
                        pat.add(p1);
                        pat.add(p2);
                        int[][] incidence = buildIncidenceMatrix(pat,bigramset);
                        cos_sim=getCosineSimilarity(incidence);
                        if(cos_sim>0.5)
                            writeResults(cos_sim,p1,p2,clusters[i],clusters[j]);
                        bigramset.clear();
                    }
                }
            }
        }


    }

}
